from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from config import config

client = Client(config.ACCOUNT_SID, config.AUTH_TOKEN)
service = client.verify.services(config.SID)


def send_verification_email(email):
    try:
        service.verifications.create(to=email, channel='email')
    except TwilioRestException:
        return False

    return True


def verify_email(email, code):
    try:
        verification_check = service.verification_checks.create(to=email, code=code)
    except TwilioRestException:
        return False

    return verification_check.valid
