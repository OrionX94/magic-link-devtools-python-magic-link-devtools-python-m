import argparse
import os
import sys

sys.path.insert(0, "src")

from magic_link_service import InfraiClient, MagicLinkRequest, MagicLinkService, render_result


parser = argparse.ArgumentParser()
parser.add_argument(
    "--email",
    default=os.environ.get("INFRAI_RECIPIENT"),
    help="recipient email (or set INFRAI_RECIPIENT)",
)
args = parser.parse_args()
if not args.email:
    parser.error("--email or INFRAI_RECIPIENT is required")

request = MagicLinkRequest(args.email, "user_demo", "checkout_demo")
release, diagnostic = MagicLinkService(InfraiClient()).start_sign_in(request)
print(render_result(release, diagnostic))
