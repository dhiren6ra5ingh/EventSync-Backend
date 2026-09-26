# EventSync API Documentation

Base URL: `http://127.0.0.1:5000`

## 0. Base Status (`/app.py`)
* **GET `/`** (Public) - Pings the server to verify it is running successfully.

## 1. Authentication (`/routes/auth_routes.py`)
* **POST `/api/register`** (Public) - Creates a new client account.
* **POST `/api/login`** (Public) - Authenticates user and returns JWT access and refresh tokens.
* **POST `/api/refresh`** (JWT Required) - Generates a new access token using a valid refresh token.

## 2. Admin & User Management (`/routes/admin_routes.py`)
* **POST `/api/admin/users`** (Admin Only) - Creates elevated accounts (admin or vendor).
* **GET `/api/vendors`** (Admin Only) - Returns a list of all registered vendors.
* **GET `/api/admin-dashboard`** (Admin Only) - Verifies admin access and returns a welcome message.
* **GET `/api/bookings`** (Admin Only) - Views all confirmed client event bookings.
* **GET `/api/analytics/summary`** (Admin Only) - Returns total counts and data for events, tasks, and budgets.
* **GET `/api/requests`** (Admin Only) - Views all support/complaint tickets submitted by clients.
* **POST `/api/requests`** (Client Only) - Submits a new support/complaint ticket.

## 3. Events (`/routes/event_routes.py`)
* **POST `/api/events`** (Admin/Vendor) - Creates a new event, checking for vendor scheduling conflicts.
* **GET `/api/events`** (JWT Required) - Retrieves a list of all events.
* **PUT `/api/events/<event_id>`** (Admin Only) - Modifies an existing event's details.
* **DELETE `/api/events/<event_id>`** (Admin Only) - Deletes an event from the database.
* **POST `/api/events/<event_id>/book`** (Client Only) - Books an event and saves it to the bookings collection.
* **GET `/api/client/event-status/<event_id>`** (Client/Admin) - Returns event progress, completed tasks, and budget overview.

## 4. Tasks (`/routes/task_routes.py`)
* **POST `/api/tasks`** (Admin Only) - Assigns a task to a vendor, checking for venue/time clashes.
* **PUT `/api/tasks/<task_id>/status`** (Vendor Only) - Updates task status to "In Progress" or "Completed".
* **GET `/api/tasks/my-tasks`** (Vendor Only) - Retrieves all tasks assigned to the currently logged-in vendor.
* **PUT `/api/tasks/<task_id>`** (Admin Only) - Modifies an existing task's details.
* **DELETE `/api/tasks/<task_id>`** (Admin Only) - Deletes a task from the database.

## 5. Budgets (`/routes/budget_routes.py`)
* **POST `/api/budgets`** (Admin Only) - Creates or updates the dynamic budget allocation for a specific event.