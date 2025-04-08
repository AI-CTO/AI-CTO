import time

from flask import jsonify, render_template, request
from openai import OpenAI

from models.models import Project, db
from services.api_assist import IdeaGenerator
from services.BMC_recources import BmcValidator as BMC #erik muutti
from services.bokeh_visualization import create_scatter_plot
from services.openai_service import extract_text_from_pdf


# test_my_function.py
def process_project(data):
    try:
        client = OpenAI()
        generator = IdeaGenerator(client)

        user_input = data.get("description")
        project_id = data.get("id")
        project_type = data.get("project_type", "Idea")  # Get project_type from input, default to "Idea"
        print("Finds description")

        if not user_input:
            return jsonify({"error": "Description is required"}), 400
        
        if project_id:
            project = Project.query.get(project_id)
            if project:
                thread_id = project.thread_id
                # Update the project_type if provided
                project.project_type = project_type
                db.session.commit()
            else:
                return jsonify({"error": "Project not found"}), 404
        else:

            thread_id = generator.create_thread()

            project = Project(
                name="Pending Evaluation",
                x_value=0,
                y_value=0,
                impact=0,
                thread_id=thread_id,
                project_type=project_type  # Save project_type
            )

            db.session.add(project)

            db.session.commit()

        # **Check if there is an active run and wait for it to finish**
        existing_runs = client.beta.threads.runs.list(thread_id=thread_id)
        print("Looking for existing runs: ", existing_runs)

        for run in existing_runs.data:
            if run.status in ["queued", "in_progress"]:
                print(f"Existing active run detected: {run.id}. Waiting...")
                timeout = 60  # 60 seconds timeout
                start_time = time.time()
                while True:
                    run_status = client.beta.threads.runs.retrieve(run_id=run.id, thread_id=thread_id)
                    print(f"Current run status: {run_status.status}")
                    if run_status.status in ["completed", "failed", "cancelled"]:
                        break
                    if time.time() - start_time > timeout:
                        print("Timeout waiting for the existing run to finish.")
                        return jsonify({"error": "Timeout waiting for existing run."}), 500
                    time.sleep(1)

        print("Done looking for existing runs")

        # **Send user input to the assistant**
        #tämä kohta lähettää käyttäjän syötteen assistantille  (User_input)
        client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=user_input
        )

        try:
            run = client.beta.threads.runs.create(
                thread_id=thread_id, assistant_id=generator.assistant_id
            )
        except Exception as e:
            print("Error starting assistant run: ", str(e))
            return jsonify({"error": "Failed to start assistant run", "details": str(e)}), 500

        # **Wait for the assistant to respond**
        print("Waiting for assistant response...")
        timeout = 60  # 60 seconds timeout
        start_time = time.time()

        while True:
            try:
                run_status = client.beta.threads.runs.retrieve(run_id=run.id, thread_id=thread_id)
                print(f"Run status: {run_status.status}")

                if run_status.status == "completed":
                    break
                if run_status.status in ["failed", "cancelled"]:
                    print("Assistant run failed or was cancelled.")
    
                    last_error = run_status.last_error
                    if last_error:
                        last_error_details = {
                            "code": getattr(last_error, "code", None),
                            "message": getattr(last_error, "message", None),
                            "type": getattr(last_error, "type", None),
                            "param": getattr(last_error, "param", None),
                        }
                    else:
                        last_error_details = None

                    return jsonify({
                        "error": "Assistant run failed or was cancelled.",
                        "details": {
                            "run_id": run_status.id,
                            "status": run_status.status,
                            "created_at": run_status.created_at,
                            "last_error": last_error_details
                        }
                    }), 500


                if time.time() - start_time > timeout:
                    print("Timeout waiting for assistant response.")
                    return jsonify({"error": "Timeout waiting for assistant response."}), 500

                time.sleep(1)
            except Exception as e:
                print("Error getting response: ", str(e))
                return jsonify({"error": "Failed to retrieve assistant response", "details": str(e)}), 500

        print("Client returned response")

        messages = client.beta.threads.messages.list(thread_id=thread_id)

        assistant_response = ""

        for message in messages.data:
            if message.role == "assistant":
                for block in message.content:
                    if hasattr(block, "text") and hasattr(block.text, "value"):
                        assistant_response += block.text.value + " "
                break

        assistant_response = assistant_response.strip() if assistant_response else "No response from the assistant."
        response_json = generator.extract_json_from_response(assistant_response)
        asistant_response = response_json.pop('assistant_response', None) #Erik Muutti
        print("tämä on assistant response \n",response_json)

        # erik Muutti 
        ans = BMC.current_vs_ideal_score(BMC,response_json)
        score = BMC.calculate_score(BMC, ans)
        # erik Muutti 
        return ( 
            jsonify(
                {
                    "message": "Chat updated",
                    "thread_id": str(thread_id),
                    "assistant_response": asistant_response, #Erik Muutti
                    "validation_score": score, #Erik Muutti
                }   
            ),
            200,
        )

    except Exception as e:
        print("Unexpected error:", str(e))
        return (
            jsonify(
                {
                    "error": "An error occurred while processing the project.",
                    "details": str(e),
                }
            ),
            500,
        )


def evaluate_project(data):
    try:
        client = OpenAI()
        generator = IdeaGenerator(client)
        thread_id = data.get("thread_id")
        project_type = data.get("project_type", "Idea")  # Get project_type from input, default to "Idea"

        if not thread_id:
            return jsonify({"error": "Missing thread_id"}), 400

        generator.thread_id = thread_id
        evaluation_result = generator.evaluate()

        if not evaluation_result:
            return jsonify({"error": "Evaluation failed"}), 500

        x_value = evaluation_result.get("x_value", 0)
        y_value = evaluation_result.get("y_value", 0)
        impact = evaluation_result.get("impact", 0)
        name = evaluation_result.get("name", "Pending Evaluation")

        project = Project.query.filter_by(thread_id=thread_id).first()

        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Update project details
        project.x_value = x_value
        project.y_value = y_value
        project.impact = impact
        project.name = name
        project.project_type = project_type  # Update project_type
        db.session.commit()

        return jsonify({"success": True, "evaluation": evaluation_result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def update_project_get(project_id):
    if not project_id:
        return render_template("update_project.html", error="Project ID is required")

    # Retrieve the project from the database
    project = Project.query.get(project_id)
    if not project:
        return render_template("update_project.html", error="Project not found")

    data = {
        "projects": [project.name],
        "business_novelty": [float(project.x_value)],
        "customer_novelty": [float(project.y_value)],
        "impact": [float(project.impact)],
        "project_types": [project.project_type],  # Include project_type
        "project_ids": [project.id],  # Include project_id
    }

    # Now pass the data to create_scatter_plot to generate the plot with one circle
    script, div = create_scatter_plot(data)

    return render_template(
        "update_project.html", project=project, script=script, div=div
    )


def update_project_post(project_id, data):
    if not project_id:
        return jsonify({"error": "Project ID is required"}), 400

    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    new_description = data.get("description")

    if new_description:
        project.name = new_description
        db.session.commit()

    return jsonify({"message": "Project updated successfully"}), 200


def resume_project(data):
    project_id = data.get("id")

    if not project_id:
        return jsonify({"error": "Project ID is required"}), 400

    try:
        project_id = int(project_id)
    except ValueError:
        return jsonify({"error": "Invalid project ID format."}), 400

    project = Project.query.get(project_id)

    if not project:
        return jsonify({"error": f"Project with ID {project_id} not found."}), 404

    thread_id = project.thread_id

    if not thread_id:
        return jsonify({"error": "No thread_id provided for this project."}), 400

    client = OpenAI()
    generator = IdeaGenerator(client)

    generator.thread_id = thread_id
    result = generator.resume_conversation()

    if "error" in result:
        return jsonify({"error": result["error"]}), 400

    return (
        jsonify(
            {
                "thread_id": thread_id,
                "message": result["message"],
            }
        ),
        200,
    )


def get_projects():
    try:
        projects = Project.query.all()
        return jsonify({"projects": [p.to_dict() for p in projects]}), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch projects", "details": str(e)}), 500


def get_project(project_id):
    try:
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


def delete_project(project_id):
    try:
        project = Project.query.get(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        db.session.delete(project)
        db.session.commit()
        return jsonify({"message": "Project deleted!"}), 200
    except Exception as e:
        return jsonify({"error": "Failed to delete project", "details": str(e)}), 500


def visualize():
    try:
        projects = Project.query.all()

        project_names = [project.name for project in projects]
        business_novelty = [float(project.x_value) for project in projects]
        customer_novelty = [float(project.y_value) for project in projects]
        impact = [float(project.impact) for project in projects]
        project_types = [project.project_type for project in projects]  # Include project_type
        project_ids = [project.id for project in projects]  # Include project_id

        data = {
            "projects": project_names,
            "business_novelty": business_novelty,
            "customer_novelty": customer_novelty,
            "impact": impact,
            "project_types": project_types,  # Pass project_type to visualization
            "project_ids": project_ids,  # Pass project_id to visualization
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


def upload_pdf(request):
    try:
        if "pdf" not in request.files:
            return jsonify({"error": "No PDF file provided"}), 400

        pdf_file = request.files["pdf"]
        extracted_text = extract_text_from_pdf(pdf_file)

        if not extracted_text:
            return jsonify({"error": "Failed to extract text from PDF"}), 500

        thread_id = request.form.get("thread_id")
        project_type = request.form.get("project_type", "Idea")  # Get project_type from form, default to "Idea"

        client = OpenAI()
        generator = IdeaGenerator(client)

        if thread_id:
            client.beta.threads.messages.create(
                thread_id=thread_id, role="user", content=extracted_text
            )
            result = generator.resume_conversation()
        else:
            thread_id = generator.create_thread()
            client.beta.threads.messages.create(
                thread_id=thread_id, role="user", content=extracted_text
            )
            result = generator.resume_conversation()

            # Include project_type when creating a new project
            project = Project(
                name="Pending Evaluation",
                x_value=0,
                y_value=0,
                impact=0,
                thread_id=thread_id,
                project_type=project_type,  # Save project_type
            )
            db.session.add(project)
            db.session.commit()

        if "error" in result:
            return jsonify({"error": result["error"]}), 400

        return jsonify({"thread_id": thread_id, "message": result["message"]}), 200

    except Exception as e:
        return jsonify({"error": "Failed to process file", "details": str(e)}), 500


def previous_projects():
    return render_template("previous_projects.html")
