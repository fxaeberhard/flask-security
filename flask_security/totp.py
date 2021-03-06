"""
    flask_security.totp
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Flask-Security TOTP (Timed-One-Time-Passwords) module

    :copyright: (c) 2019 by J. Christopher Wagner (jwag).
    :license: MIT, see LICENSE for more details.
"""

from passlib.totp import TOTP, TokenError


class Totp:
    """ Encapsulate usage of Passlib TOTP functionality.

    Flask-Security doesn't implement any replay-attack protection out of the box
    as suggested by:
    https://passlib.readthedocs.io/en/stable/narr/totp-tutorial.html#match-verify

    Subclass this and implement the get/set last_counter methods. Your subclass can
    be registered at Flask-Security creation/initialization time.

    .. versionadded:: 3.4.0

    """

    def __init__(self, secrets, issuer):
        """ Initialize a totp factory.
        secrets are used to encrypt the per-user totp_secret on disk.
        """
        # This should be a dict with at least one entry
        if not isinstance(secrets, dict) or len(secrets) < 1:
            raise ValueError("secrets needs to be a dict with at least one entry")
        self._totp = TOTP.using(issuer=issuer, secrets=secrets)

    def generate_totp_password(self, totp_secret):
        """Get time-based one-time password on the basis of given secret and time
        :param totp_secret: the unique shared secret of the user
        """
        return self._totp.from_source(totp_secret).generate().token

    def generate_totp_secret(self):
        """ Create new user-unique totp_secret.

        We return an encrypted json string so that when sent in a cookie or
        sent to DB - it is encrypted.

        """
        return self._totp.new().to_json(encrypt=True)

    def verify_totp(self, token, totp_secret, user, window=0):
        """ Verifies token for specific user.

        :param token: token to be check against user's secret
        :param totp_secret: the unique shared secret of the user
        :param user: User model
        :param window: optional. How far backward and forward in time to search
         for a match. Measured in seconds.
        :return: True if match
        """

        # TODO - in old implementation  using onetimepass window was described
        # as 'compensate for clock skew) and 'interval_length' would say how long
        # the token is good for.
        # In passlib - 'window' means how far back and forward to look and 'clock_skew'
        # is specifically for well, clock slew.
        try:
            tmatch = self._totp.verify(
                token,
                totp_secret,
                window=window,
                last_counter=self.get_last_counter(user),
            )
            self.set_last_counter(user, tmatch)
            return True

        except TokenError:
            return False

    def get_totp_uri(self, username, totp_secret):
        """ Generate provisioning url for use with the qrcode
                scanner built into the app

        :param username: username/email of the current user
        :param totp_secret: a unique shared secret of the user
        """
        tp = self._totp.from_source(totp_secret)
        return tp.to_uri(username)

    def get_last_counter(self, user):
        """ Implement this to fetch stored last_counter from cache.

        :param user: User model
        :return: last_counter as stored in set_last_counter()
        """
        return None

    def set_last_counter(self, user, tmatch):
        """ Implement this to cache last_counter.

        :param user: User model
        :param tmatch: a TotpMatch as returned from totp.verify()
        """
        pass
