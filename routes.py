import time

from flask import jsonify, render_template, request
from openai import OpenAI

from bokeh_visualization import create_scatter_plot
from models import Project, User, db
from services.openai_service import get_openai_completion
from services.test_api_assist import IdeaGenerator


def setup_routes(app):
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/process_project", methods=["POST"])
    def process_project():
        try:
            client = OpenAI()
            generator = IdeaGenerator(client)

            user_input = request.json.get("description")
            print("This is the user input", user_input)
            thread_id = request.json.get("thread_id")

            if not user_input:
                return jsonify({"error": "Description is required"}), 400

            if not thread_id:
                thread_id = generator.create_thread()

            client.beta.threads.messages.create(
                thread_id=thread_id, role="user", content=user_input
            )

            run = client.beta.threads.runs.create(
                thread_id=thread_id, assistant_id=generator.assistant_id
            )

            while True:
                run_status = client.beta.threads.runs.retrieve(
                    run_id=run.id, thread_id=thread_id  
                )
                if run_status.status == "completed":
                    break
                time.sleep(1)

            messages = client.beta.threads.messages.list(thread_id=thread_id)
            if messages.data:
                assistant_response = messages.data[0].content
            else:
                assistant_response = "No response available."
            assistant_response = (
                messages.data[0].content if messages.data else "No response available."
            )

            project_name = assistant_response.get("project_name", "Unnamed Project")
            x_value = assistant_response.get("business_novelty", 0)
            y_value = assistant_response.get("customer_novelty", 0)

            project = Project(
                name=project_name, x_value=x_value, y_value=y_value, thread_id=thread_id
            )
            db.session.add(project)
            db.session.commit()

            return (
                jsonify(
                    {
                        "message": "Conversation started",
                        "thread_id": thread_id,
                        "assistant_response": assistant_response,
                    }
                ),
                200,
            )

        except Exception as e:
            print(str(e))
            return (
                jsonify(
                    {
                        "error": "An error occurred while processing the project.",
                        "details": str(e),
                    }
                ),
                500,
            )
        
    @app.route("/continue_project", methods=["POST"])
    def continue_project():
        try:
            client = OpenAI()
            generator = IdeaGenerator(client)
            thread_id = request.json.get("thread_id")
            user_message = request.json.get("user_message")

            if not thread_id or not user_message:
                return jsonify({"error": "Both thread_id and user_message are required"}), 400

            client.beta.threads.messages.create(thread_id=thread_id, role="user", content=user_message)

            run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id=generator.assistant_id)

            while True:
                run_status = client.beta.threads.runs.retrieve(run_id=run.id, thread_id=thread_id)
                if run_status.status == "completed":
                    break
                time.sleep(1)

            messages = client.beta.threads.messages.list(thread_id=thread_id)
            assistant_response = messages.data[0].content if messages.data else "No response."

            return jsonify({
                "assistant_response": assistant_response
            }), 200

        except Exception as e:
            return jsonify({"error": "An error occurred.", "details": str(e)}), 500


    @app.route("/add_user", methods=["POST"])
    def add_user():
        try:
            data = request.get_json()
            new_user = User(**data)
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"message": "User added!", "user": new_user.to_dict()}), 201
        except Exception as e:
            return jsonify({"error": "Failed to add user", "details": str(e)}), 500

    @app.route("/get_projects", methods=["GET"])
    def get_projects():
        try:
            projects = Project.query.all()
            return jsonify({"projects": [p.to_dict() for p in projects]}), 200
        except Exception as e:
            return (
                jsonify({"error": "Failed to fetch projects", "details": str(e)}),
                500,
            )

    @app.route("/get_project", methods=["GET"])
    def get_project():
        try:
            project_id = request.args.get("id", type=str)
            if not project_id:
                return jsonify({"error": "Project ID is required"}), 400

            project = Project.query.get(project_id)
            if not project:
                return jsonify({"error": "Project not found"}), 404

            data = {
                "projects": [project.name],
                "x_value": [project.x_value],
                "y_value": [project.y_value],
                "timestamp": [project.timestamp],
            }

            script, div = create_scatter_plot(data)

            return jsonify({**project.to_dict(), "script": script, "div": div}), 200

        except Exception as e:
            return jsonify({"error": "Failed to fetch project", "details": str(e)}), 500

    @app.route("/delete_project/<int:project_id>", methods=["DELETE"])
    def delete_project(project_id):
        try:
            project = Project.query.get(project_id)
            if not project:
                return jsonify({"error": "Project not found"}), 404

            db.session.delete(project)
            db.session.commit()
            return jsonify({"message": "Project deleted!"}), 200
        except Exception as e:
            return (
                jsonify({"error": "Failed to delete project", "details": str(e)}),
                500,
            )

    @app.route("/visualize")
    def visualize():

        try:
            projects = Project.query.all()

            project_names = [project.description for project in projects]
            business_novelty = [project.returned_x_value for project in projects]
            customer_novelty = [project.returned_y_value for project in projects]
            impact = [project.impact for project in projects]

            data = {
                "projects": project_names,
                "business_novelty": business_novelty,
                "customer_novelty": customer_novelty,
                "impact": impact,
            }

            script, div = create_scatter_plot(data)
            return render_template("visualization.html", script=script, div=div)

        except Exception as e:
            return (
                jsonify(
                    {
                        "error": "An error occurred while fetching data for visualization",
                        "details": str(e),
                    }
                ),
                500,
            )

    @app.route("/previous_projects")
    def previous_projects():
        return render_template("previous_projects.html")

    @app.route("/update_project")
    def update_project():
        project_id = request.args.get("id", type=int)
        if not project_id:
            return render_template(
                "update_project.html", error="Project ID is required"
            )

        project = Project.query.get(project_id)
        if not project:
            return render_template("update_project.html", error="Project not found")

        data = {
            "projects": [project.description],
            "business_novelty": [project.returned_x_value],
            "customer_novelty": [project.returned_y_value],
            "impact": [project.impact],
            "type": [project.type],
        }

        script, div = create_scatter_plot(data)

        return render_template(
            "update_project.html", project=project, script=script, div=div
        )
