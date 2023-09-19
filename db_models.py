import json
from typing import Type

from sqlalchemy import (Boolean,Column, ForeignKey, Integer, String, Text, create_engine)
from sqlalchemy.engine import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session, sessionmaker
from sqlalchemy.dialects.postgresql import JSON

Base: Type = declarative_base()


#########################################################################################################################
################ Request ################################################################################################
#########################################################################################################################
class Request(Base):
    __tablename__ = "request"
    id = Column(Integer, primary_key=True)

    responses = relationship("Response", back_populates="request")

    method = Column(String(32), nullable=False)
    path = Column(Text, nullable=False)
    headers = Column(JSON, nullable=False)
    cookies = Column(JSON, nullable=False)
    search_params = Column(JSON, nullable=False)
    body_params = Column(JSON, nullable=False)
    is_tls = Column(Boolean, nullable=False, default=False)


#########################################################################################################################
################ Response ###############################################################################################
#########################################################################################################################
class Response(Base):
    __tablename__ = "response"
    id = Column(Integer, primary_key=True)

    code = Column(Integer)
    message = Column(String(128))
    headers = Column(JSON)
    body = Column(Text)

    request_id = Column(Integer, ForeignKey("request.id"), nullable=False)
    request = relationship("Request", back_populates="responses")


#########################################################################################################################
################ Utils ##################################################################################################
#########################################################################################################################
def load_config(filename: str):
    infile = open(filename)
    data = json.load(infile)
    infile.close()
    return data


def create_db_session(url, username, password, host, database):
    db_config = URL.create(
        url,
        username=username,
        password=password,
        host=host,
        database=database,
    )

    engine = create_engine(db_config, pool_recycle=3600, pool_size=20, max_overflow=30, pool_timeout=5)
    session_factory = sessionmaker(bind=engine)
    print("session created succesfully")
    Base.metadata.create_all(engine)

    new_db_session = scoped_session(session_factory)
    return new_db_session


def create_db_session_from_json_config_file():
    config = load_config("config.json")["db"]
    return create_db_session(config["url"], config["username"], config["password"], config["host"], config["database"])
