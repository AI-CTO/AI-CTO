import time
from flask import jsonify, render_template, request
from flask_limiter import Limiter


from controllers.project_controller import (
    process_project,
    evaluate_project,
    update_project_get,
    update_project_post,
    resume_project,
    get_projects,
    get_project,
    delete_project,
    visualize,
    previous_projects,
    upload_pdf,
)
from controllers.user_controller import user_bp

def setup_routes(app, limiter):
    MAX_DESCRIPTION_LENGTH = 700

    app.register_blueprint(user_bp)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/slow", methods=["GET"])
    @limiter.limit("4/hour")
    def slow():
        return jsonify({"Result": "This works once an hour"})

    @app.route("/process_project", methods=["POST"])
    @limiter.limit("30/hour")
    def process_project_route():
        return process_project(request.json)

    @app.route("/evaluate_project", methods=["POST"])
    @limiter.limit("10/hour")
    def evaluate_project_route():
        return evaluate_project(request.json)

    @app.route("/update_project", methods=["GET", "POST"])
    @limiter.limit("10/hour")
    def update_project_route():
        if request.method == "GET":
            return update_project_get(request.args.get("id", type=int))
        elif request.method == "POST":
            return update_project_post(request.args.get("id", type=int), request.json)

    @app.route("/resume_project", methods=["POST"])
    @limiter.limit("10/hour")
    def resume_project_route():
        return resume_project(request.json)

    @app.route("/get_projects", methods=["GET"])
    def get_projects_route():
        return get_projects()

    @app.route("/get_project", methods=["GET"])
    def get_project_route():
        return get_project(request.args.get("id", type=str))

    @app.route("/delete_project/<int:project_id>", methods=["DELETE"])
    def delete_project_route(project_id):
        return delete_project(project_id)

    @app.route("/visualize")
    def visualize_route():
        return visualize()

    @app.route("/previous_projects")
    def previous_projects_route():
        return previous_projects()

    @app.route("/upload_pdf", methods=["POST"])
    def upload_pdf_route():
        return upload_pdf(request)