from flask import jsonify, render_template, request

from bokeh_visualization import create_scatter_plot
from models import Project, User, db
from services.openai_service import get_openai_completion


def setup_routes(app):
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/process_project", methods=["POST"])
    def process_project():
        try:
            project_id = request.form.get("id")
            description = request.form.get("description")

            if not description:
                return jsonify({"error": "Missing required fields"}), 400

            existing_summary = None
            project = None

            if project_id:
                project = Project.query.get(project_id)
                if project:
                    existing_summary = project.summary

            if not existing_summary:
                existing_summary = "This is the beginning of the project's summary."

            prompt_input = f"{existing_summary}\n\n{description}"

            response_json = get_openai_completion(prompt_input)
            if response_json is None:
                return (
                    jsonify({"error": "Invalid response format from OpenAI API"}),
                    500,
                )

            print("OpenAI Response:", response_json)

            new_summary = response_json.get("summary")
            project_name = response_json["project_name"]
            business_novelty = int(response_json["business_novelty"])
            customer_novelty = int(response_json["customer_novelty"])
            impact = int(response_json["impact"])
            business_rationale = response_json["rationale_behind_business_novelty"]
            customer_rationale = response_json["rationale_behind_customer_novelty"]
            impact_rationale = response_json["rationale_behind_impact"]
            project_type = response_json["type"]

            if project:
                project.description = project_name
                project.summary = new_summary
                project.returned_x_value = business_novelty
                project.returned_y_value = customer_novelty
                project.impact = impact
                project.x_value_justification = business_rationale
                project.y_value_justification = customer_rationale
                project.type = project_type
            else:
                project = Project(
                    description=project_name,
                    summary=new_summary,
                    returned_x_value=business_novelty,
                    returned_y_value=customer_novelty,
                    impact=impact,
                    x_value_justification=business_rationale,
                    y_value_justification=customer_rationale,
                    type=project_type,
                )
                db.session.add(project)

            db.session.commit()

            return render_template(
                "index.html",
                project_name=project.description,
                business_novelty=project.returned_x_value,
                customer_novelty=project.returned_y_value,
                impact=project.impact,
                business_rationale=project.x_value_justification,
                customer_rationale=project.y_value_justification,
                impact_rationale=impact_rationale,
            )

        except Exception as e:
            return (
                jsonify(
                    {
                        "error": "An error occurred while processing the project.",
                        "details": str(e),
                    }
                ),
                500,
            )

    @app.route("/quote")
    def quote_page():
        return render_template("quote.html")

    @app.route("/quote/data", methods=["GET"])
    def quote_of_the_day():
        quote = get_openai_completion("Give me an inspirational quote of the day")
        return jsonify({"quote": quote})

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

    @app.route("/add_project", methods=["POST"])
    def add_project():
        try:
            data = request.get_json()
            new_project = Project(**data)
            print(new_project)
            db.session.add(new_project)
            db.session.commit()
            return (
                jsonify(
                    {"message": "Project added!", "project": new_project.to_dict()}
                ),
                201,
            )
        except Exception as e:
            return jsonify({"error": "Failed to add project", "details": str(e)}), 500

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
            impact = [30 for project in projects]

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
