import os
from collections import Counter
from datetime import datetime, timedelta, timezone
import json

from flask import request, Response, abort, jsonify, Blueprint
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional, verify_jwt_in_request_optional
from sqlalchemy import or_

import Hearvo.config as config
from ..app import logger, cache
from ..models import db, Post, PostSchema, VoteSelect, VoteSelectUser, UserInfoPostVoted, UserInfo, VoteMj, MjOption, VoteMjUser, Topic, PostTopic,Report,ReportReason

from .logger_api import logger_api
from Hearvo.middlewares.detect_language import get_country_id
from Hearvo.utils import cache_delete_latest_posts, cache_delete_all_posts






class ReportResource(Resource):

    @jwt_required
    def post(self):
        """
        {
            post_id: int,
            comment_id: int,
            reasons: [
                { reason: int, reason_detail: "report text" },
                { reason: int, reason_detail: "report text" },
            ]
        }
        """
        user_info_id = get_jwt_identity()
        reasons = request.json["reasons"]
        current_datetime=datetime.now(timezone(timedelta(hours=0), 'UTC')).isoformat()

        if "comment_id" in request.json.keys() :
            comment_id = request.json["comment_id"]
            add_report = Report(
                user_info_id=user_info_id,
                comment_id=comment_id,
                created_at=current_datetime, 
            )

        if "post_id" in request.json.keys() :
            post_id = request.json["post_id"]
            add_report = Report(
                user_info_id=user_info_id,
                post_id=post_id,
                created_at=current_datetime, 
            )

        try:
            db.session.add(add_report)
            db.session.flush()
            report_id = add_report.id
            
            add_reason_list = [ReportReason(report_id=report_id,reason=reason_obj["reason"], reason_detail=reason_obj["reason_detail"])
                for reason_obj in reasons]
            db.session.bulk_save_objects(add_reason_list)
            db.session.commit()
            return {"message": "Reported a content"}, 200
        except:
            db.session.rollback()
            return {"message": "Failed to report"}, 400


