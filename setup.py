from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="verse-content-sdk",
    version="0.1.0",
    author="Sanatan Learnings",
    author_email="",
    description="SDK for generating rich multimedia content for verse-based texts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sanatan-learnings/verse-content-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "elevenlabs>=1.0.0",
        "requests>=2.31.0",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        "PyYAML>=6.0.0",
        "sentence-transformers>=2.2.0",
        "torch>=2.0.0",
    ],
    entry_points={
        'console_scripts': [
            'verse-embeddings=verse_content_sdk.embeddings.generate_embeddings:main',
            'verse-audio=verse_content_sdk.audio.generate_audio:main',
            'verse-images=verse_content_sdk.images.generate_theme_images:main',
            'verse-deploy=verse_content_sdk.deployment.deploy:main',
        ],
    },
)
