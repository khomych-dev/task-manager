import factory
from app.core.security import get_password_hash
from app.models.task import Task
from app.models.user import User
from app.models.workspace import Workspace


class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker("name")
    hashed_password = factory.LazyFunction(lambda: get_password_hash("password123"))
    is_active = True


class WorkspaceFactory(factory.Factory):
    class Meta:
        model = Workspace

    name = factory.Sequence(lambda n: f"Workspace {n}")
    slug = factory.Sequence(lambda n: f"workspace-{n}")
    description = factory.Faker("sentence")


class TaskFactory(factory.Factory):
    class Meta:
        model = Task

    title = factory.Sequence(lambda n: f"Task {n}")
    description = factory.Faker("sentence")
    status = "todo"
    priority = "medium"
