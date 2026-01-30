from amanuensis.models import Project
def test_download_url_with_new_aws_version(register_user, session, login, filter_set_post, project_post, admin_user, download_urls_get, admin_update_associated_user_role):
    #dont run with normal test suit at moment
    # if True:
    #     pass
    # else:
    user_id, user_email = register_user(email=f"user1@test_download_url_with_new_aws_version.com", name="user1")
    login(user_id, user_email)
    filter_set_id = filter_set_post(
        user_id,
        name="test_download_url_with_new_aws_version",
        filter_object={"consortium":{"__type":"OPTION","selectedValues":["INSTRUCT", "INRG"],"isExclusion":False}},
        graphql_object={"AND":[{"IN":{"consortium":["INSTRUCT", "INRG"]}}]}
    ).json["id"]
    project_id = project_post(
        authorization_token=user_id,
        consortiums_to_be_returned_from_pcdc_analysis_tools=["INSTRUCT", "INRG"],
        description="test_download_url_with_new_aws_version",
        institution="test_download_url_with_new_aws_version",
        associated_users_emails=[],
        name="test_download_url_with_new_aws_version",
        filter_set_ids=[filter_set_id]
    ).json["id"]

    admin_update_associated_user_role(
        authorization_token=admin_user[0], 
        user_id=user_id,
        project_id=project_id,
        role="DATA_ACCESS"
    )

    session.query(Project).filter(Project.id == project_id).update({"approved_url": "https://gen3-helm-pelican-export.s3.amazonaws.com/test.json"})
    session.commit()

    login(user_id, user_email)
    assert download_urls_get(
        authorization_token=user_id,
        project_id=project_id,
        status_code=200
    )

    session.query(Project).filter(Project.id == project_id).update({"approved_url": "https://gen3-helm-pelican-export.s3.us-east-1.amazonaws.com/test.json"})
    session.commit()

    login(user_id, user_email)
    assert download_urls_get(
        authorization_token=user_id,
        project_id=project_id,
        status_code=200
    )

