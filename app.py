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
                    # Insert coupon
                    cursor.execute(
                        'INSERT IGNORE INTO coupons (coupon_code) VALUES (%s)',
                        (coupon,)
                    )
                    
                    # Log generation
                    ip_address = request.remote_addr or 'unknown'
                    cursor.execute(
                        'INSERT INTO usage_logs (coupon_code, ip_address) VALUES (%s, %s)',
                        (coupon, ip_address)
                    )
                    
                connection.commit()
                print("✅ Coupon stored in database")
                db_message = "Coupon stored successfully"
                
            except Exception as e:
                print(f"⚠️ Failed to store coupon: {e}")
                db_status = "error"
                db_message = f"Storage error: {str(e)}"
            finally:
                connection.close()
        else:
            print(f"⚠️ Running without database storage: {db_message}")
        
        # Render template
        return render_template('index.html', 
                             coupon=coupon, 
                             db_status=db_status,
                             db_message=db_message,
                             status="generated")
        
    except Exception as e:
        print(f"💥 Critical error in home route: {e}")
        print(traceback.format_exc())
        # Fallback response
        return f"""
        <html>
        <html lang="en">
        <head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Coupon Generator | AWS RDS MySQL</title>

  <!-- Orbitron Futuristic Font -->
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600&display=swap" rel="stylesheet">

  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: 'Orbitron', sans-serif;
      background: radial-gradient(circle at top left, #0f0f1b, #000);
      color: #fff;
      padding: 20px;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
    }

    .container {
      background: rgba(255, 255, 255, 0.05);
      padding: 40px;
      border-radius: 20px;
      box-shadow: 0 10px 30px rgba(0, 255, 255, 0.1);
      text-align: center;
      max-width: 650px;
      width: 100%;
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    h1 {
      color: #00ffe7;
      margin-bottom: 10px;
      font-size: 2.5em;
      text-shadow: 0 0 5px #00ffe7;
    }

    .subtitle {
      color: #aaa;
      margin-bottom: 30px;
      font-size: 1em;
    }

    .logo {
      font-size: 3em;
      margin-bottom: 10px;
      text-shadow: 0 0 10px #00ffe7;
    }

    .coupon-display {
      background: linear-gradient(135deg, #00ffe7, #0088ff);
      color: #000;
      padding: 25px;
      border-radius: 15px;
      font-size: 2em;
      font-weight: bold;
      letter-spacing: 3px;
      margin: 20px 0;
      border: 2px dashed rgba(255, 255, 255, 0.3);
      box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: transform 0.3s ease;
      word-break: break-word;
      animation: neonPulse 2s infinite;
    }

    .coupon-display:hover { transform: scale(1.02); }

    @keyframes neonPulse {
      0% { box-shadow: 0 0 10px #00ffe7; }
      50% { box-shadow: 0 0 25px #00ffe7; }
      100% { box-shadow: 0 0 10px #00ffe7; }
    }

    .stats {
      background: rgba(255,255,255,0.05);
      padding: 20px;
      border-radius: 15px;
      margin: 25px 0;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 15px;
    }

    .stat-item { text-align: center; }

    .stat-value {
      font-size: 1.8em;
      color: #00ffd9;
      margin-bottom: 5px;
      text-shadow: 0 0 5px #00ffd9;
    }

    .stat-label { font-size: 0.85em; color: #ccc; }

    .generate-btn {
      background: linear-gradient(135deg, #00ffe7, #006eff);
      color: black;
      border: none;
      padding: 15px 40px;
      font-size: 1.2em;
      border-radius: 50px;
      cursor: pointer;
      transition: all 0.3s ease;
      font-weight: bold;
      letter-spacing: 1px;
      margin: 15px 0;
      box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
    }

    .generate-btn:hover {
      transform: scale(1.05);
      box-shadow: 0 0 25px rgba(0, 255, 255, 0.7);
    }

    .generate-btn:disabled {
      background: #333;
      color: #999;
      cursor: not-allowed;
      box-shadow: none;
    }

    .db-status {
      margin-top: 20px;
      padding: 12px;
      border-radius: 8px;
      font-weight: bold;
      font-size: 0.95em;
      background: rgba(255, 255, 255, 0.05);
    }

    .db-connected { color: #00ffcc; border-left: 5px solid #00ffcc; }
    .db-disconnected { color: #ff4c4c; border-left: 5px solid #ff4c4c; }
    .db-error { color: #ffcc00; border-left: 5px solid #ffcc00; }

    .notification {
      position: fixed;
      top: 20px;
      right: 20px;
      background: #00ffe7;
      color: #000;
      padding: 15px 20px;
      border-radius: 10px;
      box-shadow: 0 0 15px rgba(0,255,255,0.5);
      opacity: 0;
      transform: translateX(100px);
      transition: all 0.3s ease;
      font-weight: 600;
    }

    .notification.active { opacity: 1; transform: translateX(0); }
    .notification.error { background: #ff4c4c; color: #fff; }

    .app-info {
      margin-top: 20px;
      font-size: 0.85em;
      color: #aaa;
      background: rgba(255, 255, 255, 0.02);
      padding: 10px;
      border-radius: 10px;
      border-left: 3px solid #00ffe7;
    }

    .app-info a { color: #00ffe7; text-decoration: underline; }

    @media (max-width: 600px) {
      .container { padding: 25px 20px; }
      h1 { font-size: 2em; }
      .coupon-display { font-size: 1.6em; padding: 20px; }
      .generate-btn { font-size: 1em; padding: 12px 25px; }
    }
  </style>
</head>

<body>
  <div class="container">
    <div class="logo">🤖</div>
    <h1>Coupon Generator</h1>
    <div class="subtitle">AWS RDS MySQL Database | DB: coupon-db</div>

    <div class="stats" id="statsDisplay">
      <div class="stat-item">
        <div class="stat-value" id="totalCoupons">-</div>
        <div class="stat-label">Total Coupons</div>
      </div>
      <div class="stat-item">
        <div class="stat-value" id="todayCoupons">-</div>
        <div class="stat-label">Today</div>
      </div>
      <div class="stat-item">
        <div class="stat-value" id="availableCoupons">-</div>
        <div class="stat-label">Available</div>
      </div>
      <div class="stat-item">
        <div class="stat-value" id="recentCoupons">-</div>
        <div class="stat-label">Recent (1h)</div>
      </div>
    </div>

    <div class="coupon-display" id="couponDisplay" title="Click to copy coupon">
      {{ coupon }}
    </div>

    <button class="generate-btn" onclick="generateNewCoupon()" id="generateBtn">
      🔄 Generate New Coupon
    </button>

    <div class="db-status db-{{ db_status }}" id="dbStatus">
      {% if db_status == 'connected' %}
        ✅ Database Connected - coupon-db
      {% elif db_status == 'error' %}
        ⚠️ Database Error - coupon-db
      {% else %}
        ❌ Database Disconnected - coupon-db
      {% endif %}
    </div>

    <div class="app-info">
      <p>Built with 💻 Flask + AWS RDS MySQL</p>
      <p>GitHub: <a href="#" target="_blank">YourProjectLink</a></p>
    </div>
  </div>

  <div class="notification" id="notification">Coupon copied to clipboard!</div>

  <script>
    // Copy coupon code
    const couponDisplay = document.getElementById('couponDisplay');
    const notification = document.getElementById('notification');

    couponDisplay.addEventListener('click', () => {
      const text = couponDisplay.textContent.trim();
      navigator.clipboard.writeText(text);
      notification.classList.add('active');
      setTimeout(() => notification.classList.remove('active'), 2000);
    });

    // Generate new coupon via API
    async function generateNewCoupon() {
      const btn = document.getElementById('generateBtn');
      btn.disabled = true;
      btn.textContent = 'Generating...';
      try {
        const res = await fetch('/generate');
        const data = await res.json();
        couponDisplay.textContent = data.coupon;
      } catch (err) {
        notification.textContent = 'Error generating coupon!';
        notification.classList.add('active', 'error');
        setTimeout(() => {
          notification.classList.remove('active', 'error');
          notification.textContent = 'Coupon copied to clipboard!';
        }, 3000);
      } finally {
        btn.disabled = false;
        btn.textContent = '🔄 Generate New Coupon';
      }
    }
  </script>
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
