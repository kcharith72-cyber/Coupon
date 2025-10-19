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
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coupon Generator | AWS RDS MySQL</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .container {
            background: rgba(255, 255, 255, 0.95);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 650px;
            width: 100%;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
            font-weight: 700;
        }

        .subtitle {
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 1.1em;
        }

        .logo {
            font-size: 3em;
            margin-bottom: 10px;
        }

        .coupon-display {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            padding: 25px;
            border-radius: 15px;
            font-size: 2.2em;
            font-weight: bold;
            letter-spacing: 3px;
            margin: 20px 0;
            border: 3px dashed rgba(255, 255, 255, 0.5);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            min-height: 120px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            cursor: pointer;
            word-break: break-all;
        }

        .coupon-display:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.3);
        }

        .stats {
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin: 25px 0;
            font-size: 1.1em;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
        }

        .stat-item {
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 0.85em;
            opacity: 0.9;
            text-align: center;
        }

        .generate-btn {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            border: none;
            padding: 18px 40px;
            font-size: 1.3em;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 15px 0;
            box-shadow: 0 5px 15px rgba(255, 107, 107, 0.3);
            font-weight: 600;
            letter-spacing: 1px;
            width: 100%;
            max-width: 300px;
        }

        .generate-btn:hover {
            background: linear-gradient(45deg, #ee5a24, #ff6b6b);
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(255, 107, 107, 0.4);
        }

        .generate-btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .db-status {
            margin-top: 20px;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 0.95em;
        }

        .db-connected {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .db-disconnected {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .db-error {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }

        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            z-index: 1000;
            opacity: 0;
            transform: translateX(100px);
            transition: all 0.3s ease;
            max-width: 350px;
            font-weight: 600;
        }

        .notification.active {
            opacity: 1;
            transform: translateX(0);
        }

        .notification.error {
            background: #f44336;
        }

        .loading {
            opacity: 0.7;
            pointer-events: none;
        }

        .pulse {
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.02); }
            100% { transform: scale(1); }
        }

        .app-info {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            font-size: 0.9em;
            color: #6c757d;
            border-left: 4px solid #6c757d;
        }

        @media (max-width: 600px) {
            .container {
                padding: 25px 20px;
                margin: 10px;
            }
            
            h1 {
                font-size: 2em;
            }
            
            .coupon-display {
                font-size: 1.8em;
                padding: 20px;
                letter-spacing: 2px;
            }
            
            .generate-btn {
                padding: 15px 30px;
                font-size: 1.1em;
                max-width: 100%;
            }
            
            .stats {
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
                padding: 15px;
            }
            
            .stat-value {
                font-size: 1.5em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🎫</div>
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

        <div class="coupon-display pulse" id="couponDisplay" title="Click to copy coupon">
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
            <strong>Application Info:</strong> 
            Click coupon to copy | Auto-refresh every 30s | 
            <a href="/health" target="_blank">Health Check</a> | 
            <a href="/stats" target="_blank">API Stats</a>
        </div>
    </div>

    <!-- Notification -->
    <div class="notification" id="notification">
        ✅ Your coupon is ready!
    </div>

    <script>
        let currentCoupon = "{{ coupon }}";
        let isGenerating = false;

        function generateNewCoupon() {
            if (isGenerating) return;
            
            isGenerating = true;
            const generateBtn = document.getElementById('generateBtn');
            const couponDisplay = document.getElementById('couponDisplay');
            const container = document.querySelector('.container');
            
            // Show loading state
            generateBtn.disabled = true;
            generateBtn.innerHTML = '⏳ Generating...';
            couponDisplay.textContent = 'Generating...';
            couponDisplay.style.background = 'linear-gradient(45deg, #ffa726, #ff9800)';
            container.classList.add('loading');
            
            fetch('/generate')
                .then(response => response.json())
                .then(data => {
                    if (data.coupon) {
                        currentCoupon = data.coupon;
                        couponDisplay.textContent = data.coupon;
                        couponDisplay.style.background = 'linear-gradient(45deg, #4CAF50, #45a049)';
                        showNotification('🎉 New coupon generated!');
                        updateStats(); // Refresh stats
                    } else {
                        throw new Error('No coupon received');
                    }
                })
                .catch(error => {
                    console.error('Error generating coupon:', error);
                    couponDisplay.textContent = 'Error - Try Again';
                    couponDisplay.style.background = 'linear-gradient(45deg, #f44336, #d32f2f)';
                    showNotification('❌ Failed to generate coupon', true);
                })
                .finally(() => {
                    generateBtn.disabled = false;
                    generateBtn.innerHTML = '🔄 Generate New Coupon';
                    container.classList.remove('loading');
                    isGenerating = false;
                });
        }

        function showNotification(message, isError = false) {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = 'notification' + (isError ? ' error' : '');
            notification.classList.add('active');
            
            setTimeout(() => {
                notification.classList.remove('active');
            }, 3000);
        }

        function updateStats() {
            fetch('/stats')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('statsDisplay').innerHTML = 
                            '<div class="stat-item"><div class="stat-label">Statistics unavailable</div></div>';
                        updateDbStatus('error');
                    } else {
                        document.getElementById('totalCoupons').textContent = data.total_coupons?.toLocaleString() || '0';
                        document.getElementById('todayCoupons').textContent = data.today_coupons?.toLocaleString() || '0';
                        document.getElementById('availableCoupons').textContent = data.available_coupons?.toLocaleString() || '0';
                        document.getElementById('recentCoupons').textContent = data.recent_coupons?.toLocaleString() || '0';
                        
                        updateDbStatus(data.database_status || 'connected');
                    }
                })
                .catch(error => {
                    console.error('Error fetching stats:', error);
                    updateDbStatus('disconnected');
                });
        }

        function updateDbStatus(status) {
            const dbStatus = document.getElementById('dbStatus');
            dbStatus.className = 'db-status db-' + status;
            
            switch(status) {
                case 'connected':
                    dbStatus.innerHTML = '✅ Database Connected - coupon-db';
                    break;
                case 'error':
                    dbStatus.innerHTML = '⚠️ Database Error - coupon-db';
                    break;
                default:
                    dbStatus.innerHTML = '❌ Database Disconnected - coupon-db';
            }
        }

        // Copy coupon to clipboard when clicked
        document.getElementById('couponDisplay').addEventListener('click', function() {
            if (currentCoupon && currentCoupon !== 'Generating...' && currentCoupon !== 'Error - Try Again') {
                navigator.clipboard.writeText(currentCoupon).then(() => {
                    showNotification('✅ Coupon copied to clipboard!');
                }).catch(() => {
                    // Fallback for older browsers
                    const textArea = document.createElement('textarea');
                    textArea.value = currentCoupon;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    showNotification('✅ Coupon copied to clipboard!');
                });
                
                // Click animation
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 150);
            }
        });

        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', function() {
            updateStats();
            setTimeout(() => {
                if (currentCoupon && currentCoupon !== '') {
                    showNotification('🎉 Your coupon is ready! Click to copy.');
                }
            }, 1000);
            
            // Update stats every 30 seconds
            setInterval(updateStats, 30000);
            
            // Add keyboard shortcut (Ctrl+G or Cmd+G) to generate coupon
            document.addEventListener('keydown', function(e) {
                if ((e.ctrlKey || e.metaKey) && e.key === 'g') {
                    e.preventDefault();
                    generateNewCoupon();
                }
            });
        });
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
