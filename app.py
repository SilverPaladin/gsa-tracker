from flask import Flask, render_template_string

app = Flask(__name__)

# HTML Template with embedded CSS to ensure fixed positioning
page_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Staff Portal</title>
    <style>
        /* BASE STYLES */
        body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            box-sizing: border-box;
        }

        /* TOP MENU: Fixed at the top, spans full width */
        .top-menu {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 60px;
            background-color: #2c3e50; /* Dark Blue */
            color: white;
            display: flex;
            align-items: center;
            padding: 0 20px;
            z-index: 1000; /* Ensures it stays on top of everything */
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }

        .top-menu button {
            background-color: #34495e;
            color: white;
            border: 1px solid #7f8c8d;
            padding: 8px 15px;
            margin-right: 10px;
            cursor: pointer;
            border-radius: 4px;
        }

        .top-menu button:hover {
            background-color: #1abc9c;
        }

        /* LEFT MENU: Fixed to the left, starts below top menu */
        .left-menu {
            position: fixed;
            top: 60px; /* Pushes it down by the height of the top menu */
            left: 0;
            bottom: 0; /* Stretches to bottom of screen */
            width: 200px;
            background-color: #34495e; /* Slightly lighter blue */
            color: white;
            padding: 20px;
            overflow-y: auto; /* Allows menu to scroll internally if buttons exceed height */
            z-index: 900;
        }

        .left-menu button {
            display: block;
            width: 100%;
            background-color: transparent;
            color: white;
            border: none;
            text-align: left;
            padding: 15px 10px;
            cursor: pointer;
            border-bottom: 1px solid #7f8c8d;
        }

        .left-menu button:hover {
            background-color: #2c3e50;
            padding-left: 15px; /* slight animation effect */
            transition: 0.2s;
        }

        /* MAIN CONTENT: Pushed over and down to clear the menus */
        .main-content {
            margin-top: 60px; /* Clear top menu */
            margin-left: 200px; /* Clear left menu */
            padding: 40px;
            background-color: #ecf0f1;
            min-height: 200vh; /* FORCED HEIGHT TO DEMONSTRATE SCROLLING */
        }
    </style>
</head>
<body>

    <div class="top-menu">
        <h3 style="margin-right: 30px;">STAFF PORTAL</h3>
        <button>Dashboard</button>
        <button>Notifications</button>
        <button>Profile</button>
        <button>Settings</button>
        <button>Logout</button>
    </div>

    <div class="left-menu">
        <button>Employee List</button>
        <button>Time Off Requests</button>
        <button>Payroll</button>
        <button>Performance Reviews</button>
