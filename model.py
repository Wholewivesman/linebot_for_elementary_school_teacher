from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    pass


class SuperUser(Base):
    __tablename__ = "super_user"
    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(50))

    def __repr__(self) -> str:
        return f"UserInfo(id={self.id!r}, uid={self.uid!r}, name={self.name!r}"


class UserInfo(Base):
    __tablename__ = "user_info"
    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(50))
    points: Mapped[int] = mapped_column()
    currentQid: Mapped[int] = mapped_column()

    def __repr__(self) -> str:
        return f"UserInfo(id={self.id!r}, uid={self.uid!r}, name={self.name!r}, currentQid={self.currentQid!r})"


class UserAns(Base):
    __tablename__ = "user_ans"
    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[str] = mapped_column(String(50))
    qid: Mapped[int] = mapped_column()
    ans: Mapped[str] = mapped_column(String(1))

    def __repr__(self) -> str:
        return f"User_ans(id={self.id!r}, uid={self.uid!r}, qid={self.qid!r}, ans={self.ans!r})"