"""
Twitterログインで作成されたユーザーにsuperuser権限を付与するコマンド
"""
import os
import sys

from django.contrib.auth import get_user_model
from django.contrib.auth.management import get_default_username
from django.core import exceptions
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS
from django.utils.functional import cached_property
from django.utils.text import capfirst


class NotRunningInTTYException(Exception):
    pass


class Command(BaseCommand):
    help = "Used to grant a superuser."
    requires_migrations_checks = True
    stealth_options = ("stdin",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.UserModel = get_user_model()
        self.username_field = self.UserModel._meta.get_field(self.UserModel.USERNAME_FIELD)

    def add_arguments(self, parser):
        parser.add_argument(
            "--%s" % self.UserModel.USERNAME_FIELD,
            help="Specifies the login for the superuser.",
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help=(
                "Tells Django to NOT prompt the user for input of any kind. "
                "You must use --%s with --noinput, along with an option for "
                "any other required field. Superusers created with --noinput will "
                "not be able to log in until they're given a valid password."
                % self.UserModel.USERNAME_FIELD
            ),
        )
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help='Specifies the database to use. Default is "default".',
        )

    def execute(self, *args, **options):
        self.stdin = options.get("stdin", sys.stdin)  # Used for testing
        return super().execute(*args, **options)

    def handle(self, *args, **options):
        username = options[self.UserModel.USERNAME_FIELD]
        database = options["database"]
        user_data = {}
        verbose_field_name = self.username_field.verbose_name

        try:
            if options["interactive"]:
                # Same as user_data but without many to many fields and with
                # foreign keys as fake model instances instead of raw IDs.
                fake_user_data = {}
                if hasattr(self.stdin, "isatty") and not self.stdin.isatty():
                    raise NotRunningInTTYException
                default_username = get_default_username(database=database)
                if username:
                    error_msg = self._validate_username(username, verbose_field_name, database)
                    if error_msg:
                        self.stderr.write(error_msg)
                        username = None
                elif username == "":
                    raise CommandError("%s cannot be blank." % capfirst(verbose_field_name))
                # Prompt for username.
                while username is None:
                    message = self._get_input_message(self.username_field, default_username)
                    username = self.get_input_data(self.username_field, message, default_username)
                    if username:
                        error_msg = self._validate_username(username, verbose_field_name, database)
                        if error_msg:
                            self.stderr.write(error_msg)
                            username = None
                            continue
                user_data[self.UserModel.USERNAME_FIELD] = username
                fake_user_data[self.UserModel.USERNAME_FIELD] = (
                    self.username_field.remote_field.model(username)
                    if self.username_field.remote_field
                    else username
                )
            else:
                # Non-interactive mode.
                # Use username from environment variable, if not provided in
                # options.
                if username is None:
                    username = os.environ.get(
                        "DJANGO_SUPERUSER_" + self.UserModel.USERNAME_FIELD.upper()
                    )
                if username is None:
                    raise CommandError(
                        "You must use --%s with --noinput." % self.UserModel.USERNAME_FIELD
                    )
                else:
                    error_msg = self._validate_username(username, verbose_field_name, database)
                    if error_msg:
                        raise CommandError(error_msg)

                user_data[self.UserModel.USERNAME_FIELD] = username

            user = self.UserModel._default_manager.db_manager(database).get_by_natural_key(
                username
            )
            user.is_staff = True
            user.is_superuser = True
            user.save()

            if options["verbosity"] >= 1:
                self.stdout.write("Superuser granted successfully.")
        except KeyboardInterrupt:
            self.stderr.write("\nOperation cancelled.")
            sys.exit(1)
        except exceptions.ValidationError as e:
            raise CommandError("; ".join(e.messages))
        except NotRunningInTTYException:
            self.stdout.write(
                "Superuser creation skipped due to not running in a TTY. "
                "You can run `manage.py createsuperuser` in your project "
                "to create one manually."
            )

    def get_input_data(self, field, message, default=None):
        """
        Override this method if you want to customize data inputs or
        validation exceptions.
        """
        raw_value = input(message)
        if default and raw_value == "":
            raw_value = default
        try:
            val = field.clean(raw_value, None)
        except exceptions.ValidationError as e:
            self.stderr.write("Error: %s" % "; ".join(e.messages))
            val = None

        return val

    def _get_input_message(self, field, default=None):
        return "%s%s%s: " % (
            capfirst(field.verbose_name),
            " (leave blank to use '%s')" % default if default else "",
            " (%s.%s)"
            % (
                field.remote_field.model._meta.object_name,
                field.m2m_target_field_name()
                if field.many_to_many
                else field.remote_field.field_name,
            )
            if field.remote_field
            else "",
        )

    @cached_property
    def username_is_unique(self):
        if self.username_field.unique:
            return True
        return any(
            len(unique_constraint.fields) == 1
            and unique_constraint.fields[0] == self.username_field.name
            for unique_constraint in self.UserModel._meta.total_unique_constraints
        )

    def _validate_username(self, username, verbose_field_name, database):
        """Validate username. If invalid, return a string error message."""
        if self.username_is_unique:
            try:
                self.UserModel._default_manager.db_manager(database).get_by_natural_key(username)
            except self.UserModel.DoesNotExist:
                return "Error: That %s does not exist." % verbose_field_name
        if not username:
            return "%s cannot be blank." % capfirst(verbose_field_name)
        try:
            self.username_field.clean(username, None)
        except exceptions.ValidationError as e:
            return "; ".join(e.messages)
