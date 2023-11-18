import datetime

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column


class Base(DeclarativeBase, MappedAsDataclass):
    # Base.metadata will store the information of all the tables that inherit this class
    pass


class User(Base):
    __tablename__ = "botuser"  # table name is changed because "botuser" is a reserved keyword in PostgreSQL

    # id will be automatically assigned by the database, so it should not be initialized in the constructor
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    slack_user_id: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]


class RA(Base):
    __tablename__ = "ra"

    # id will be automatically assigned by the database, so it should not be initialized in the constructor
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    ra_name: Mapped[str]


class TimeCard(Base):
    __tablename__ = "timecard"

    # id will be automatically assigned by the database, so it should not be initialized in the constructor
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    ra_id: Mapped[int] = mapped_column(
        ForeignKey("ra.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    start_time: Mapped[datetime.datetime]
    end_time: Mapped[datetime.datetime] = mapped_column(
        CheckConstraint("end_time > start_time", name="time_integrity")
    )
    duration: Mapped[datetime.time]
