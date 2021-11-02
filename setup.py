import pathlib
import setuptools


LOCATION = pathlib.Path(__file__).parent.resolve()


def read_requirements():
    """parses requirements from requirements.txt"""
    reqs_file = LOCATION / "requirements.txt"
    reqs = [line.strip() for line in reqs_file.open(encoding="utf8").readlines() if not line.strip().startswith("#")]

    names = []
    links = []
    for req in reqs:
        if "://" in req:
            links.append(req)
        else:
            names.append(req)
    return {"install_requires": names, "dependency_links": links}


readme_file = LOCATION / "README.md"
long_description = readme_file.open(encoding="utf8").read()

setuptools.setup(
    name="dff_node_stats",
    version="0.1.a1",
    scripts=[],
    author="Denis Kuznetsov",
    author_email="kuznetsov.den.p@gmail.com",
    description="Statistics collection extension for Dialog Flow Framework "
    "(https://github.com/deepmipt/dialog_flow_framework).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    package_data={},
    include_package_data=True,
    extras_require={
        "api": ["fastapi>=0.68.0", "uvicorn>=0.14.0"],
        "dashboard": ["streamlit>=0.85.1", "graphviz>=0.17"],
        "all": ["fastapi>=0.68.0", "uvicorn>=0.14.0", "streamlit>=0.85.1", "graphviz==0.17"],
    },
    **read_requirements()
)
