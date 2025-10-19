from flask import Flask, jsonify, render_template, request
import math
import random
import os
import pymysql
from datetime import datetime
import time
import traceback
import socket

app = Flask(__name__)

# Database configuration - UPDATED DATABASE NAME
DB_CONFIG = {
    'host': 'coupon-db.c18swy2galw4.eu-west-1.rds.amazonaws.com',
    'user': 'admin', 
    'password': 'CouponApp123!',
    'database': 'coupon_db',  # ← CHANGED TO coupon_db (with underscore)
    'port': 3306,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'connect_timeout': 10
}

def get_db_connection():
    """Create database connection with detailed error reporting"""
    try:
        print(f"🔗 Connecting to {DB_CONFIG['host']}...")
        connection = pymysql.connect(**DB_CONFIG)
        print("✅ Database connection successful")
        return connection, "Connected successfully"
    except pymysql.MySQLError as e:
        error_code = e.args[0]
        error_message = e.args[1] if len(e.args) > 1 else str(e)
        
        print(f"❌ MySQL Error {error_code}: {error_message}")
        
        # Common error codes and their meanings
        error_messages = {
            1045: "Access denied - check username/password",
            1049: f"Database '{DB_CONFIG['database']}' does not exist",
            2003: "Cannot connect to MySQL server - check security groups and public access",
            1044: "Access denied for database - check user permissions",
            2005: "Unknown MySQL server host - check RDS endpoint",
            1698: "Access denied for user - authentication plugin issue"
        }
        
        user_message = error_messages.get(error_code, error_message)
        return None, user_message
        
    except Exception as e:
        print(f"❌ Unexpected connection error: {e}")
        return None, f"Unexpected error: {str(e)}"

def init_database():
    """Initialize database tables"""
    print("🔄 Attempting database initialization...")
    
    connection, message = get_db_connection()
    if not connection:
        print(f"💥 Cannot initialize database: {message}")
        return False, message
    
    try:
        with connection.cursor() as cursor:
            # Create coupons table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS coupons (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    coupon_code VARCHAR(50) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    used BOOLEAN DEFAULT FALSE,
                    used_at TIMESTAMP NULL
                )
            ''')
            print("✅ Coupons table ready")
            
            # Create usage_logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    coupon_code VARCHAR(50) NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45)
                )
            ''')
            print("✅ Usage_logs table ready")
            
        connection.commit()
        print("🎉 Database initialization completed successfully")
        return True, "Database initialized successfully"
        
    except Exception as e:
        error_msg = f"Database initialization failed: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg
    finally:
        connection.close()

def generate_coupon_code():
    """Generate a unique coupon code"""
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))

def simulate_cpu_load():
    """Simulate moderate CPU load"""
    for i in range(1, 10000):
        math.sqrt(i)

@app.route('/')
def home():
    """Main page route"""
    try:
        # Simulate CPU load
        simulate_cpu_load()
        
        # Generate coupon
        coupon = generate_coupon_code()
        print(f"🎫 Generated coupon: {coupon}")
        
        # Try to store in database
        connection, db_message = get_db_connection()
        db_status = "connected" if connection else "disconnected"
        
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute('INSERT IGNORE INTO coupons (coupon_code) VALUES (%s)', (coupon,))
                    ip_address = request.remote_addr or 'unknown'
                    cursor.execute('INSERT INTO usage_logs (coupon_code, ip_address) VALUES (%s, %s)', (coupon, ip_address))
                connection.commit()
                db_message = "Coupon stored successfully"
            except Exception as e:
                print(f"⚠️ Failed to store coupon: {e}")
                db_status = "error"
                db_message = f"Storage error: {str(e)}"
            finally:
                connection.close()
        else:
            print(f"⚠️ Running without database storage: {db_message}")
        
        return render_template('index.html', 
                             coupon=coupon, 
                             db_status=db_status,
                             db_message=db_message,
                             status="generated")

    except Exception as e:
        print(f"💥 Critical error in home route: {e}")
        print(traceback.format_exc())
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Coupon Generator</title>
    <style>
        :root {{
            --bg-light: #f9f9f9;
            --bg-dark: #0f1419;
            --text-light: #333;
            --text-dark: #f0f0f0;
            --primary: #007BFF;
            --primary-hover: #0056b3;
            --accent: #009688;
            --card-light: #ffffff;
            --card-dark: #1c1f24;
            --shadow-light: rgba(0, 0, 0, 0.1);
            --shadow-dark: rgba(0, 0, 0, 0.5);
        }}

        @media (prefers-color-scheme: dark) {{
            body {{
                background: var(--bg-dark);
                color: var(--text-dark);
            }}
            .container {{
                background: var(--card-dark);
                box-shadow: 0 6px 25px var(--shadow-dark);
            }}
            .coupon-box {{
                background: var(--accent);
                color: #fff;
            }}
            .status {{
                background: rgba(255, 255, 255, 0.05);
                color: #ccc;
            }}
            .button {{
                background-color: var(--primary);
                color: #fff;
            }}
            .button:hover {{
                background-color: var(--primary-hover);
            }}
            .nav-links a {{
                color: #66b2ff;
            }}
            .nav-links a:hover {{
                color: #99ccff;
            }}
        }}

        @media (prefers-color-scheme: light) {{
            body {{
                background: linear-gradient(135deg, #e0f7fa, var(--bg-light));
                color: var(--text-light);
            }}
            .container {{
                background: var(--card-light);
                box-shadow: 0 6px 20px var(--shadow-light);
            }}
            .coupon-box {{
                background: var(--accent);
                color: #fff;
            }}
            .status {{
                background: #f0f0f0;
                color: #333;
            }}
            .button {{
                background-color: var(--primary);
                color: #fff;
            }}
            .button:hover {{
                background-color: var(--primary-hover);
            }}
            .nav-links a {{
                color: var(--primary);
            }}
            .nav-links a:hover {{
                color: var(--primary-hover);
            }}
        }}

        body {{
            font-family: 'Poppins', Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            transition: background 0.4s ease, color 0.4s ease;
        }}

        .container {{
            border-radius: 16px;
            padding: 40px;
            width: 90%;
            max-width: 520px;
            text-align: center;
            transition: transform 0.2s ease, box-shadow 0.3s ease;
        }}

        .container:hover {{
            transform: translateY(-3px);
        }}

        h1 {{
            font-size: 1.9em;
            color: var(--accent);
            margin-bottom: 10px;
        }}

        .subtitle {{
            font-size: 0.95em;
            opacity: 0.8;
            margin-bottom: 25px;
        }}

        .coupon-box {{
            padding: 20px 25px;
            border-radius: 10px;
            margin: 20px 0;
        }}

        .coupon-label {{
            font-size: 1em;
            opacity: 0.9;
            margin-bottom: 5px;
        }}

        .coupon-code {{
            font-size: 2em;
            font-weight: 600;
            letter-spacing: 1px;
        }}

        .status {{
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
        }}

        .status p {{
            margin: 8px 0;
            font-size: 0.95em;
        }}

        .button {{
            margin-top: 25px;
            padding: 12px 28px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            transition: background 0.3s ease, transform 0.1s ease;
        }}

        .button:hover {{
            transform: scale(1.03);
        }}

        .nav-links {{
            margin-top: 25px;
            font-size: 0.95em;
        }}

        .nav-links a {{
            margin: 0 10px;
            text-decoration: none;
            transition: color 0.2s ease;
        }}

        .footer {{
            margin-top: 30px;
            font-size: 0.8em;
            opacity: 0.6;
        }}
    </style>
</head>

<body>
    <div class="container">
        <h1>🎫 Coupon Generator</h1>
        <p class="subtitle">Generate unique coupons and check your AWS RDS MySQL status.</p>

        <div class="coupon-box">
            <div class="coupon-label">Your Coupon Code:</div>
            <div class="coupon-code">{coupon}</div>
        </div>

        <div class="status">
            <p><strong>Database Status:</strong> {db_status}</p>
            <p><strong>Message:</strong> {db_message}</p>
        </div>

        <button class="button" onclick="window.location.reload()">🔄 Generate New Coupon</button>

        <div class="nav-links">
            <a href="/stats">📊 Stats</a>
            <a href="/health">❤️ Health</a>
            <a href="/debug">🐛 Debug</a>
        </div>

        <div class="footer">© 2025 CouponGen | Flask + AWS RDS</div>
    </div>
</body>
</html>
"""


@app.route('/generate')
def generate_coupon():
    """API endpoint to generate a new coupon"""
    try:
        simulate_cpu_load()
        coupon = generate_coupon_code()
        
        connection, db_message = get_db_connection()
        db_status = "connected" if connection else "disconnected"
        
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        'INSERT IGNORE INTO coupons (coupon_code) VALUES (%s)',
                        (coupon,)
                    )
                    
                    ip_address = request.remote_addr or 'unknown'
                    cursor.execute(
                        'INSERT INTO usage_logs (coupon_code, ip_address) VALUES (%s, %s)',
                        (coupon, ip_address)
                    )
                    
                connection.commit()
                db_message = "Coupon generated and stored"
            except Exception as e:
                print(f"❌ Failed to store coupon: {e}")
                db_status = "error"
                db_message = f"Storage error: {str(e)}"
            finally:
                connection.close()
        else:
            db_message = "Running in offline mode - coupon not stored"
        
        return jsonify({
            'coupon': coupon,
            'status': 'generated',
            'database': db_status,
            'message': db_message,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"💥 Error in generate route: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def stats():
    """Get coupon statistics"""
    connection, db_message = get_db_connection()
    
    if not connection:
        return jsonify({
            'total_coupons': 0,
            'used_coupons': 0,
            'today_coupons': 0,
            'available_coupons': 0,
            'database_status': 'disconnected',
            'message': db_message,
            'running_mode': 'offline'
        })
    
    try:
        with connection.cursor() as cursor:
            # Total coupons
            cursor.execute('SELECT COUNT(*) as total FROM coupons')
            total = cursor.fetchone()['total'] or 0
            
            # Used coupons
            cursor.execute('SELECT COUNT(*) as used FROM coupons WHERE used = TRUE')
            used = cursor.fetchone()['used'] or 0
            
            # Today's coupons
            cursor.execute('SELECT COUNT(*) as today FROM coupons WHERE DATE(created_at) = CURDATE()')
            today = cursor.fetchone()['today'] or 0
            
            # Recent coupons (last hour)
            cursor.execute('SELECT COUNT(*) as recent FROM coupons WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)')
            recent = cursor.fetchone()['recent'] or 0
            
        return jsonify({
            'total_coupons': total,
            'used_coupons': used,
            'today_coupons': today,
            'recent_coupons': recent,
            'available_coupons': total - used,
            'database_status': 'connected',
            'message': 'Database connected successfully'
        })
        
    except Exception as e:
        print(f"❌ Error in stats: {e}")
        return jsonify({
            'error': str(e),
            'database_status': 'error'
        }), 500
    finally:
        if connection:
            connection.close()

@app.route('/health')
def health():
    """Health check endpoint"""
    connection, db_message = get_db_connection()
    db_status = "connected" if connection else "disconnected"
    
    # Test database functionality if connected
    db_test = False
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1 as test')
                result = cursor.fetchone()
                db_test = result['test'] == 1
            connection.close()
        except Exception as e:
            db_message = f"Database test failed: {str(e)}"
            db_status = "error"
    
    overall_status = 'healthy' if db_status == 'connected' and db_test else 'unhealthy'
    
    return jsonify({
        'status': overall_status,
        'database': db_status,
        'database_test': db_test,
        'database_message': db_message,
        'timestamp': datetime.now().isoformat(),
        'application': 'running',
        'rds_endpoint': DB_CONFIG['host'],
        'database_name': DB_CONFIG['database']
    })

@app.route('/debug')
def debug():
    """Debug information endpoint"""
    connection, db_message = get_db_connection()
    
    debug_info = {
        'application': 'running',
        'database_connection': 'connected' if connection else 'failed',
        'database_message': db_message,
        'rds_endpoint': DB_CONFIG['host'],
        'database_name': DB_CONFIG['database'],
        'timestamp': datetime.now().isoformat(),
        'flask_debug': app.debug
    }
    
    if connection:
        try:
            with connection.cursor() as cursor:
                # Get table list
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                debug_info['tables'] = [list(table.values())[0] for table in tables]
                
                # Get record counts
                if 'coupons' in debug_info['tables']:
                    cursor.execute("SELECT COUNT(*) as count FROM coupons")
                    debug_info['coupons_count'] = cursor.fetchone()['count']
                
                if 'usage_logs' in debug_info['tables']:
                    cursor.execute("SELECT COUNT(*) as count FROM usage_logs")
                    debug_info['usage_logs_count'] = cursor.fetchone()['count']
                    
                # Get database version
                cursor.execute("SELECT VERSION() as version")
                debug_info['mysql_version'] = cursor.fetchone()['version']
                
        except Exception as e:
            debug_info['database_error'] = str(e)
        finally:
            connection.close()
    
    return jsonify(debug_info)

@app.route('/coupons')
def list_coupons():
    """List recent coupons (for debugging)"""
    connection, db_message = get_db_connection()
    
    if not connection:
        return jsonify({'error': 'Database connection failed', 'message': db_message}), 500
    
    try:
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT coupon_code, created_at, used 
                FROM coupons 
                ORDER BY created_at DESC 
                LIMIT 20
            ''')
            coupons = cursor.fetchall()
            
        return jsonify({
            'coupons': coupons,
            'count': len(coupons),
            'database_status': 'connected'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        connection.close()

# Initialize application
print("🚀 Starting Coupon Application...")
print(f"📊 RDS Endpoint: {DB_CONFIG['host']}")
print(f"🔑 Database: {DB_CONFIG['database']}")
print(f"👤 Username: {DB_CONFIG['user']}")

# Initialize database
init_success, init_message = init_database()
if init_success:
    print("✅ Database initialization completed")
else:
    print(f"⚠️ Database initialization: {init_message}")
    print("🔄 Application will run in mixed mode")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Starting Flask application on port {port}")
    print("✅ Application is ready!")
    app.run(host='0.0.0.0', port=5000, debug=True)
