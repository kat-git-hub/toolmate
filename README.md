# Toolmate App

**ToolMate** is a web application that allows people to rent tools from their neighbors instead of buying them. Whether you're doing a one-time project or need something temporarily, ToolMate helps you save money, reduce waste, and build community.

[![Maintainability](https://api.codeclimate.com/v1/badges/25d8e43843087ec87384/maintainability)](https://codeclimate.com/github/kat-git-hub/toolmate/maintainability)   [![Test Coverage](https://api.codeclimate.com/v1/badges/25d8e43843087ec87384/test_coverage)](https://codeclimate.com/github/kat-git-hub/toolmate/test_coverage)   [![CI](https://github.com/kat-git-hub/toolmate/actions/workflows/CI.yml/badge.svg)](https://github.com/kat-git-hub/toolmate/actions/workflows/CI.yml)


## Features

- 🔍 Filter and search tools by:
  - Name
  - Category
  - Price range
  - Availability
- 🗺️ Interactive map with user pins showing available tools by location
- 📄 Tool cards with descriptions and images
- 🔐 User registration and login system
- 🧰 Users can add, edit, and delete their own tools
- 📦 Rent and return tools
- 📊 Pagination and backend filtering for efficient performance

## Tech Stack

- **Backend:** Flask, SQLAlchemy, Jinja2
- **Frontend:** HTML, CSS (Bootstrap), JavaScript, Leaflet.js (for the map)
- **Database:** SQLite / PostgreSQL
- **Testing:** Pytest

## Quick Start Guide

1. Clone the repository:
```
git clone https://github.com/kat-git-hub/toolmate.git
cd toolmate 
```

2. Install dependencies
Make sure Poetry is installed, then run:
```
make install
```
3. Set up environment variables
Create a .env file in the project root and add your settings:
```
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your_secret_key
```
4. Run the development server
```
make runserver
```
Your app should now be running at http://127.0.0.1:8000
