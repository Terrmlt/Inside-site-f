# База лицензий на недропользование

## Overview
This project is a Django-based web application designed to manage a database of subsurface use licenses. It features an interactive Yandex.Map for visualizing licenses, detailed license information through modal windows, and document upload/download functionality. The application aims to provide a comprehensive tool for tracking and managing mineral extraction licenses, offering filtering, search capabilities, and GeoJSON map integration. It is built with a focus on ease of use for administrators and clear visualization for all users, with an eye towards future integration with external databases and LDAP authentication for enterprise environments.

## Recent Changes
- **November 1, 2025:** Complete design modernization inspired by professional financial websites (Hodge Bank style):
  - Removed all emoji icons for a clean, professional appearance
  - Implemented modern Inter font family from Google Fonts
  - Created gradient header with dark blue/navy color scheme (#1a365d, #0f2540)
  - Enhanced UI components with modern shadows, rounded corners, and smooth transitions
  - Improved license cards with hover effects and professional styling
  - Updated modal windows with gradient headers and refined layouts
  - Applied professional color palette with CSS custom properties for consistency
  - All components now use modern design patterns with improved spacing and typography

## User Preferences
I prefer simple language and clear explanations. I like iterative development and want the agent to ask before making major changes. I prefer detailed explanations for complex tasks. Do not make changes to the `media/` folder. Do not make changes to the `create_test_data.py` file without explicit instruction. **Design preference:** Professional, clean design without childish elements like emojis - inspired by modern financial websites.

## System Architecture
The application is a Django web application.
- **UI/UX:** The interface features a modern, professional design with a clean layout displaying an interactive Yandex.Map and control panel with license cards. Modals are used for detailed license information. The design uses Inter font family, a professional color scheme (dark navy blue gradient header, accent blue #0066cc), and modern UI patterns with smooth transitions and shadows. Bootstrap 5 and Vanilla JavaScript are used for the frontend.
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