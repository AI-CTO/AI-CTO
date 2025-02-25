import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from flask import Flask
from openai import OpenAI

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

from app import create_app
from models.models import Project, db
from src.routes import setup_routes
from src.services.api_assist import IdeaGenerator




def init_generator():
    client = OpenAI()
    generator = IdeaGenerator(client)
    return generator


class TestAssistant(unittest.TestCase):

    def setUp(self):
        self.generator = init_generator()
        file_path = os.path.join(os.path.dirname(__file__), "mockBusinessPlan.txt")
        with open(file_path, "r") as file:
            self.business_plan = file.read()

    def test_create_assistant(self):
        self.generator = init_generator()
        assistant_id = self.generator.create_assistant()
        beginning = assistant_id.split("_")[0]

        assert isinstance(assistant_id, str)
        assert beginning == "asst"

    def test_create_thread(self):
        self.generator = init_generator()
        thread_id = self.generator.create_thread()
        beginning = thread_id.split("_")[0]

        assert isinstance(thread_id, str)
        assert beginning == "thread"
