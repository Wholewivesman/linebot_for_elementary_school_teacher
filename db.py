from sqlalchemy.orm import Session
from sqlalchemy import create_engine, and_
from model import UserInfo, Base, UserAns
import json

engine = create_engine("sqlite:///./db.db", echo=True)


def createUserInfo(profile):
    with Session(engine) as session:
        session.add(
            UserInfo(
                uid=profile.user_id, name=profile.display_name, currentQid=0, points=0
            )
        )
        session.commit()


def getUserInfo(user_id):
    with Session(engine) as session:
        return session.query(UserInfo).filter(UserInfo.uid == user_id).first()


def calcPoints(user_id):
    with Session(engine) as session:
        thisUserInfo = session.query(UserInfo).filter(UserInfo.uid == user_id).first()
        thisUserAns = session.query(UserAns).filter(UserAns.uid == user_id).all()
        questionsDict = json.load(open("./questions.json", "r"))
        number = questionsDict["number"]
        questions = questionsDict["questions"]
        correctNum = 0
        for a in thisUserAns:
            if questions[a.qid - 1]["ans"] == a.ans:
                correctNum += 1
        score = correctNum * 100 // number
        thisUserInfo.points = score
        session.commit()


def incCurrentQid(user_id):
    with Session(engine) as session:
        session.query(UserInfo).filter(UserInfo.uid == user_id).update(
            {"currentQid": UserInfo.currentQid + 1}
        )
        session.commit()


def getQuestionDict():
    return json.load(open("./questions.json", "r"))


def getQuestion(qid):
    questionsDict = getQuestionDict()
    number = questionsDict["number"]
    if qid > number:
        return None
    questions = questionsDict["questions"]
    return questions[qid - 1]


def getUserAns(uid, qid):
    with Session(engine) as session:
        return (
            session.query(UserAns)
            .filter(and_(UserAns.uid == uid, UserAns.qid == qid))
            .first()
        )


def addUserAns(uid, qid, ans):
    with Session(engine) as session:
        session.add(UserAns(uid=uid, qid=qid, ans=ans))
        session.commit()


def getUserRankingAsc():
    qNum = getQuestionDict()["number"]
    with Session(engine) as session:
        return (
            session.query(UserInfo)
            .order_by(UserInfo.points.desc())
            .filter(UserInfo.currentQid > qNum)
            .all()
        )


def initDB():
    Base.metadata.create_all(engine)
