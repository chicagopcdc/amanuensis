import sys
import os

# Add /amanuensis/amanuensis to the path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "amanuensis"))
)

from amanuensis import app_init, app

app_init(app)
application = app
