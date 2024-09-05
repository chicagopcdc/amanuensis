import json
import uuid
import logging
import html2text

from boto3 import client
from boto3.exceptions import Boto3Error
from botocore.exceptions import ClientError

from amanuensis.config import config as amanuensis_config
from amanuensis.errors import UserError, InternalError, UnavailableError, NotFound


class BotoManager(object):
    """
    AWS manager singleton.
    """

    URL_EXPIRATION_DEFAULT = 1800  # 30 minutes
    URL_EXPIRATION_MAX = 86400  # 1 day

    def __init__(self, config, logger):
        self.sts_client = client("sts", **config)
        self.s3_client = client("s3", **config)
        self.logger = logger
        self.ec2 = None
        self.iam = None

    def delete_data_file(self, bucket, prefix):
        """
        We use buckets with versioning disabled.

        See AWS docs here:

            https://docs.aws.amazon.com/AmazonS3/latest/dev/DeletingObjectsfromVersioningSuspendedBuckets.html
        """
        try:
            s3_objects = self.s3_client.list_objects_v2(
                Bucket=bucket, Prefix=prefix, Delimiter="/"
            )

            if not s3_objects.get("Contents"):
                # file not found in the bucket
                self.logger.info(
                    "tried to delete prefix {} but didn't find in bucket {}".format(
                        prefix, bucket
                    )
                )
                return (
                    "Unable to delete the data file associated with this record. Backing off.",
                    404,
                )
            if len(s3_objects["Contents"]) > 1:
                self.logger.error("multiple files found with prefix {}".format(prefix))
                return ("Multiple files found matching this prefix. Backing off.", 400)
            key = s3_objects["Contents"][0]["Key"]
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            self.logger.info(
                "deleted file for prefix {} in bucket {}".format(prefix, bucket)
            )
            return ("", 204)
        except (KeyError, Boto3Error) as e:
            self.logger.error("Failed to delete file: {}".format(str(e)))
            return ("Unable to delete data file.", 500)

    def assume_role(self, role_arn, duration_seconds, config=None):
        assert (
            duration_seconds
        ), 'assume_role() cannot be called without "duration_seconds" parameter; please check your "expires_in" parameters'
        try:
            if config and "aws_access_key_id" in config:
                self.sts_client = client("sts", **config)
            session_name_postfix = uuid.uuid4()
            return self.sts_client.assume_role(
                RoleArn=role_arn,
                DurationSeconds=duration_seconds,
                RoleSessionName="{}-{}".format("gen3", session_name_postfix),
            )
        except Boto3Error as ex:
            self.logger.exception(ex)
            raise InternalError("Fail to assume role: {}".format(ex))
        except Exception as ex:
            self.logger.exception(ex)
            raise UnavailableError("Fail to reach AWS: {}".format(ex))

    def presigned_url(self, bucket, key, expires, config, method="get_object"):
        """
        Args:
            bucket (str): bucket name
            key (str): key in bucket
            expires (int): presigned URL expiration time, in seconds
            config (dict): additional parameters if necessary (e.g. updating access key)
            method (str): "get_object" or "put_object" (ClientMethod argument to boto)
        """
        if method not in ["get_object"]:  # , "put_object"]:
            raise UserError("method {} not allowed".format(method))
        if "aws_access_key_id" in config:
            self.s3_client = client("s3", **config)

        expires = int(expires) or self.URL_EXPIRATION_DEFAULT
        expires = min(expires, self.URL_EXPIRATION_MAX)
        params = {"Bucket": bucket, "Key": key}
        if method == "put_object":
            params["ServerSideEncryption"] = "AES256"

        try:
            return self.s3_client.generate_presigned_url(
                ClientMethod=method, Params=params, ExpiresIn=expires
            )
        except Exception as ex:
            self.logger.exception(ex)
            raise InternalError("Failed to get pre-signed url")

        # import boto3
        # AWS_S3_REGION = 'ap-south-1'
        # AWS_S3_BUCKET_NAME = "my_s3_bucket"
        # AWS_S3_FILE_NAME = "my-file.jpg"
        # PRESIGNED_URL_EXPIRY = 100 # in seconds
        # s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, region_name=AWS_S3_REGION, aws_secret_access_key=AWS_SECRET_ACCESS_KEY,)
        # presigned_url = s3_client.generate_presigned_url('get_object',    Params={"Bucket": AWS_S3_BUCKET_NAME, "Key": AWS_S3_FILE_NAME}, ExpiresIn=PRESIGNED_URL_EXPIRY)
        # s3_client = boto3.client('s3',region_name="ap-south-1",config=boto3.session.Config(signature_version='s3v4',))
        # s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': object_name}, ExpiresIn=expiration)

    def get_bucket_region(self, bucket, config):
        try:
            if "aws_access_key_id" in config:
                self.s3_client = client("s3", **config)
            response = self.s3_client.get_bucket_location(Bucket=bucket)
            region = response.get("LocationConstraint")
        except Boto3Error as ex:
            self.logger.exception(ex)
            raise InternalError("Fail to get bucket region: {}".format(ex))
        except Exception as ex:
            self.logger.exception(ex)
            raise UnavailableError("Fail to reach AWS: {}".format(ex))
        if region is None:
            return "us-east-1"
        return region

    def get_all_groups(self, list_group_name):
        """
        Get all group listed in the list_group_name.
        If group does not exist, add as new group and include in the return list
        :param list_group_name:
        :return:
        """
        try:
            groups = self.get_user_group(list_group_name)
            if len(groups) < len(list_group_name):
                for group_name in list_group_name:
                    if group_name not in groups:
                        groups[group_name] = self.create_user_group(group_name)
        except Exception as ex:
            self.logger.exception(ex)
            raise UserError("Fail to create list of groups: {}".format(ex))
        return groups

    def add_user_to_group(self, groups, username):
        """
        Add user to the list of group which have association membership.
        :param groups:
        :param username:
        :return:
        """
        try:
            for group in list(groups.values()):
                self.iam.add_user_to_group(
                    GroupName=group["GroupName"], UserName=username
                )
        except Exception as ex:
            self.logger.exception(ex)
            raise UserError("Fail to add user to group: {}".format(ex))

    def get_user_group(self, group_names):
        try:
            groups = self.iam.list_groups()["Groups"]
            res = {}
            for group in groups:
                if group["GroupName"] in group_names:
                    res[group["GroupName"]] = group
        except Exception as ex:
            self.logger.exception(ex)
            raise UserError("Fail to get list of groups {}: {}".format(group_names, ex))
        return res

    def create_user_group(self, group_name, path=None):
        try:
            group = self.iam.create_group(GroupName=group_name)["Group"]
            self.__create_policy__(
                group_name, self.__get_policy_document_by_group_name__(group_name)
            )
        except Exception as ex:
            self.logger.exception(ex)
            raise UserError("Fail to create group {}: {}".format(group_name, ex))
        return group

    def __get_policy_document_by_group_name__(self, group_name):
        """
        Getting policy document from config file and replace with actual value (same as project name)
        :param group_name:
        :return:
        """
        pass

    def __fill_with_new_value__(self, document, value):
        pass

    def __create_policy__(
        self, policy_name, policy_document, path=None, description=None
    ):
        """
        Create policy with name and policies specified in policy_document.
        :param policy_name: Name of policy in AWS.
        :param policy_document: Document specified the policy rule.
        :param path:
        :param description:
        :return:
        """
        try:
            aws_kwargs = dict(Path=path, Description=description)
            aws_kwargs = {k: v for k, v in list(aws_kwargs.items()) if v is not None}
            policy = self.iam.create_policy(
                PolicyName=policy_name, PolicyDocument=policy_document, **aws_kwargs
            )
            self.iam.attach_group_policy(
                GroupName=policy_name, PolicyArn=policy["Policy"]["Arn"]
            )
        except Exception as ex:
            self.logger.exception(ex)
            raise UserError("Fail to create policy: {}".format(ex))
        return policy

    def send_email_ses(self, body, to_emails, subject):
        """
        Send email to group of emails using AWS SES api.

        Args:
            body: html or text message
            to_emails(list): list of emails to receive the messages
            subject(str): email subject
            smtp_domain(dict): smtp domain server

        Returns:
            Http response

        Exceptions:
            KeyError

        """

        # TODO add import for boto

        if not amanuensis_config["AWS_CREDENTIALS"]["SES"]:
            raise NotFound(
                "AWS SES '{}' does not exist in configuration. Cannot send email."
            )
        if "SENDER" not in amanuensis_config["AWS_CREDENTIALS"]:
            raise NotFound(
                "AWS SES sender does not exist in configuration. Cannot send email."
            )
        if (
            "AWS_ACCESS_KEY" not in amanuensis_config["AWS_CREDENTIALS"]["SES"]
            or "AWS_SECRET_KEY" not in amanuensis_config["AWS_CREDENTIALS"]["SES"]
        ):
            raise NotFound(
                "AWS SES credentials are missing in configuration. Cannot send email."
            )

        # TODO retrieve body from template (pass as external param above)
        if not body:
            raise Exception("You must provide a text or html body.")
        if not subject:
            raise Exception("You must provide a text subject for the email.")

        sender = amanuensis_config["AWS_CREDENTIALS"]["SENDER"]
        region = (
            amanuensis_config["AWS_CREDENTIALS"]["SES"]["AWS_REGION"]
            if amanuensis_config["AWS_CREDENTIALS"]["SES"]["AWS_REGION"] is not None
            else "us-east-1"
        )
        AWS_ACCESS_KEY = amanuensis_config["AWS_CREDENTIALS"]["SES"]["AWS_ACCESS_KEY"]
        AWS_SECRET_KEY = amanuensis_config["AWS_CREDENTIALS"]["SES"]["AWS_SECRET_KEY"]

        # if body is in html format, strip out html markup
        # otherwise body and body_text could have the same values
        body_text = html2text.html2text(body)

        # if not self._html:
        #     self._format = 'text'
        #     body = self._text

        logging.info("Config: {}".format(amanuensis_config))

        boto3_client = client(
            "ses",
            region_name=region,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
        )
        response = "Failed to send email."
        try:
            response = boto3_client.send_email(
                Destination={
                    "ToAddresses": to_emails,
                },
                Message={
                    "Body": {
                        "Text": {
                            "Charset": "UTF-8",
                            "Data": body_text,
                        },
                        "Html": {
                            "Charset": "UTF-8",
                            "Data": body,
                        },
                    },
                    "Subject": {
                        "Charset": "UTF-8",
                        "Data": subject,
                    },
                },
                Source=sender,
            )
        except ClientError as e:
            print(e.response["Error"]["Message"])
        else:
            print("Email sent! Message ID:"),
            print(response["MessageId"])
        return response
