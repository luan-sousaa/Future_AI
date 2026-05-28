from src.observability.phoenix import setup_phoenix


def bootstrap_app(
    project_name: str
) -> None:
    setup_phoenix(
        project_name=project_name
    )
