import pathlib
import setuptools


LOCATION = pathlib.Path(__file__).parent.resolve()

readme_file = LOCATION / "README.md"
long_description = readme_file.open(encoding="utf8").read()

setuptools.setup(
    name="dff_node_stats",
    version="0.1.a3",
    scripts=[],
    author="Denis Kuznetsov",
    author_email="kuznetsov.den.p@gmail.com",
    description="Statistics collection extension for Dialog Flow Framework "
    "(https://github.com/deepmipt/dialog_flow_framework).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kudep/dff-node-stats",
    packages=setuptools.find_packages(where="."),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    extras_require={
        "api": ["fastapi>=0.68.0", "uvicorn>=0.14.0"],
        "dashboard": ["streamlit>=1.1.0", "graphviz==0.17"],
        "all": ["fastapi>=0.68.0", "uvicorn>=0.14.0", "streamlit>=1.1.0", "graphviz==0.17"],
    },
    install_requires=["pandas>=1.3.1", "dff>=0.1a5"],
)
