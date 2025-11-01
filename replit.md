# База лицензий на недропользование

## Overview
This project is a Django-based web application designed to manage a database of subsurface use licenses. It features an interactive Yandex.Map for visualizing licenses, detailed license information through modal windows, and document upload/download functionality. The application aims to provide a comprehensive tool for tracking and managing mineral extraction licenses, offering filtering, search capabilities, and GeoJSON map integration. It is built with a focus on ease of use for administrators and clear visualization for all users, with an eye towards future integration with external databases and LDAP authentication for enterprise environments.

## Recent Changes
- **November 1, 2025 (Latest):** Complete redesign in Orrivo style - modern, light, and clean:
  - Switched to light color scheme with white background and dark text for better readability
  - Added hero section with dark gradient background featuring large typography
  - Implemented live statistics dashboard (total licenses, active licenses, regions, license types)
  - Redesigned license cards with large typography, SVG icons, and metadata grid layout
  - Created clean white navigation header with subtle shadows
  - Updated color palette: accent orange (#ff6b35), neutral grays, clean whites
  - Added section headers with centered titles and subtitles
  - Implemented modern card hover effects with translateY animations
  - Enhanced modal windows with gradient headers and refined styling
- **November 1, 2025:** Initial design modernization - removed all emoji icons for professional appearance, implemented Inter font family, created professional color palette with CSS custom properties

## User Preferences
I prefer simple language and clear explanations. I like iterative development and want the agent to ask before making major changes. I prefer detailed explanations for complex tasks. Do not make changes to the `media/` folder. Do not make changes to the `create_test_data.py` file without explicit instruction. **Design preference:** Modern, light, clean design inspired by contemporary property websites like Orrivo - featuring large typography, white backgrounds, statistics dashboards, and SVG icons.

## System Architecture
The application is a Django web application.
- **UI/UX:** The interface features a modern Orrivo-inspired design with:
  - Hero section with dark gradient background (#1a1a1a to #2d2d2d) and large white typography
  - Live statistics dashboard showing total licenses, active count, regions, and license types
  - Clean white navigation header with subtle shadows
  - Light color scheme (white #ffffff background, dark #1a1a1a text, accent orange #ff6b35)
  - License cards with large typography, SVG icons, and metadata grid showing region, type, and minerals
  - Interactive Yandex.Map with 600px height and rounded corners
  - Section headers with centered titles and descriptive subtitles
  - Bootstrap 5, Vanilla JavaScript, and Inter font family for the frontend
- **Technical Implementations:**
    - **Interactive Map:** Displays licenses using Yandex.Maps JavaScript API 2.1, with markers and polygons (colored by mineral usage type, e.g., БЭ, БП, БР)
    - **Data Management:** CRUD operations for `License` and `Document` models, accessible via Django Admin and API endpoints.
    - **Filtering & Search:** Licenses can be filtered by status, region, type, and mineral, and searched by license number and user.
    - **Document Management:** Upload and download functionality for documents linked to licenses.
    - **GeoJSON Integration:** Web and admin interfaces allow for uploading GeoJSON files, which automatically update or create license data, parse information, determine regions, and calculate polygon centers.
    - **Authentication:** Django's built-in authentication is used, with placeholders for LDAP integration.
    - **Database:** PostgreSQL is configured as the production database, with SQLite for development.
- **Feature Specifications:**
    - **License Model:** Stores unique license number, mineral usage type, user, coordinates, region, dates, mineral type, status, and description.
    - **Document Model:** Links to a license, stores document name, file, type, upload date, and user.
- **System Design Choices:**
    - **Modularity:** The project is organized into `mineral_licenses` (project settings) and `licenses` (core application) Django apps.
    - **API Endpoints:** Provides RESTful API for licenses (`GET /api/licenses/`, `GET /api/licenses/<id>/`) and documents (`POST /api/licenses/<id>/upload/`, `GET /api/documents/<id>/download/`).
    - **Environment Configuration:** Uses environment variables for sensitive data (`SECRET_KEY`, `YANDEX_MAPS_API_KEY`) and database connection.

## External Dependencies
- **Database:** PostgreSQL (via Neon on Replit), SQLite (for development).
- **Mapping Service:** Yandex.Maps JavaScript API 2.1.
- **Web Server:** Gunicorn.
- **Dependency Management:** uv.
- **Frontend Framework:** Bootstrap 5.
- **Authentication (planned):** `django-auth-ldap` for LDAP integration.