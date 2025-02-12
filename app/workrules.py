import datetime
from typing import Optional

from .db.model import TimeCard


class WorkRules:
    """A set of methods used to ensure a work record follows work rules for all RAs."""

    @classmethod
    def generate_warning_about_recess_hours(cls, record: TimeCard) -> Optional[str]:
        """Check if recess hours are enough.
        RAs should take recess depending on their work hours in a day.

        Args:
            record (TimeCard): a record of work.

        Returns:
            Optional[str]: returns a warning message if recess hours are too short.
        """

        if record.duration > datetime.time(
            hour=6
        ) and record.break_duration < datetime.time(hour=1):
            return ":warning: Recess hours are too short. If you work more than 6 hours, you must take 1 hour's recess."

    @classmethod
    def generate_warning_about_report_timing(cls, record: TimeCard) -> Optional[str]:
        """Check if the gap between `end_time` of the work and the report timing is larger than 24 hours.
        RAs are encouraged to report their work on time.

        Args:
            record (TimeCard): a record of work.

        Returns:
            Optional[str]: returns a warning message if the gap is larger than 24 hours.
        """

        if (datetime.datetime.now() - record.end_time) > datetime.timedelta(days=1):
            return ":stopwatch: More than 24 hours have already passed since you finished your work. Let's try to report on time!"

    @classmethod
    def generate_warnings_about_all_rules(cls, record: TimeCard) -> list[str]:
        """Check if violation from any of the work rules is found.

        Args:
            record (TimeCard): a record of work.

        Returns:
            list[str]: returns warning messages, if any.
        """
        warnings: list[str] = []
        for f in [
            cls.generate_warning_about_recess_hours,
            cls.generate_warning_about_report_timing,
        ]:
            if warning := f(record=record):
                warnings.append(warning)
        return warnings
