<?php
/*
Plugin Name: Strom Tarif Shortcodes
Plugin URI: 
Description: Ein Plugin, das Shortcodes für Stromtariflisten und Diagramme bereitstellt
Version: 1.0.3
Author: dev@gwen.at
Author URI: https://skale.dev
*/

// Sicherheitscheck
if (!defined('ABSPATH')) {
    exit;
}

class StromTarifPlugin {
    private $api_url = 'https://skaledev-servestromtarifeendpoint.web.val.run/';
    private $cache_time = 3600; // 1 Stunde Cache-Zeit

    public function __construct() {
        add_shortcode('tarifliste', array($this, 'tarifliste_shortcode'));
        add_shortcode('diagrammxyz', array($this, 'diagramm_shortcode'));
        add_action('wp_enqueue_scripts', array($this, 'enqueue_styles'));
    }

    public function enqueue_styles() {
        wp_enqueue_style('stromtarif-styles', plugins_url('css/style.css', __FILE__));
    }

    private function get_tarif_data($rows = 10) {
        // Cache-Key generieren
        $cache_key = 'stromtarife_' . $rows;
        
        // Prüfen ob Daten im Cache sind
        $cached_data = get_transient($cache_key);
        if ($cached_data !== false) {
            return $cached_data;
        }

        // API-URL mit Parametern
        $request_url = add_query_arg(array(
            'contentformat' => 'json',
            'rows' => $rows
        ), $this->api_url);

        // API-Anfrage
        $response = wp_remote_get($request_url);

        if (is_wp_error($response)) {
            return array('error' => $response->get_error_message());
        }

        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            return array('error' => 'Ungültige Daten vom API-Endpunkt');
        }

        // Daten im Cache speichern
        set_transient($cache_key, $data, $this->cache_time);

        return $data;
    }

    public function tarifliste_shortcode($atts) {
        $atts = shortcode_atts(array(
            'rows' => 10,
            'layout' => 'table', // table oder cards
        ), $atts);

        $tarife = $this->get_tarif_data($atts['rows']);

        if (isset($tarife['error'])) {
            return '<div class="error-message">' . esc_html($tarife['error']) . '</div>';
        }

        if ($atts['layout'] === 'cards') {
            $output = $this->render_cards_layout($tarife);
        $output .= $this->render_attribution();
        return $output;
        }

        $output = $this->render_table_layout($tarife);
        $output .= $this->render_attribution();
        return $output;
    }

    private function render_table_layout($tarife) {
        ob_start();
        ?>
        <div class="stromtarife-table-container">
            <table class="stromtarife-table">
                <thead>
                    <tr>
                        <th>Anbieter</th>
                        <th>Tarif</th>
                        <th>Art</th>
                        <th>Anpassung</th>
                        <th>Preis</th>
                        <th>Info</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($tarife as $tarif): ?>
                    <tr>
                        <td><?php echo esc_html($tarif['stromanbieter']); ?></td>
                        <td><?php echo esc_html($tarif['tarifname']); ?></td>
                        <td><?php echo esc_html($tarif['tarifart']); ?></td>
                        <td><?php echo esc_html($tarif['preisanpassung']); ?></td>
                        <td><?php echo esc_html($tarif['strompreis']); ?></td>
                        <td><?php echo esc_html($tarif['kurzbeschreibung']); ?></td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
        <?php
        $output = ob_get_clean();
        return $output;
    }

    private function render_attribution() {
        return sprintf(
            '<p class="stromtarife-attribution">Data by <a href="%s" target="_blank" rel="noopener noreferrer">%s</a> / <a href="%s" target="_blank" rel="noopener noreferrer">%s</a></p>',
            'https://gwen.at',
            'gwen.at',
            'https://skale.dev',
            'skale.dev'
        );
    }

    private function render_cards_layout($tarife) {
        ob_start();
        ?>
        <div class="stromtarife-cards">
            <?php foreach ($tarife as $tarif): ?>
            <div class="tarif-card">
                <div class="tarif-header">
                    <h3><?php echo esc_html($tarif['tarifname']); ?></h3>
                    <span class="anbieter"><?php echo esc_html($tarif['stromanbieter']); ?></span>
                </div>
                <div class="tarif-body">
                    <div class="tarif-price"><?php echo esc_html($tarif['strompreis']); ?></div>
                    <div class="tarif-details">
                        <p><strong>Art:</strong> <?php echo esc_html($tarif['tarifart']); ?></p>
                        <p><strong>Anpassung:</strong> <?php echo esc_html($tarif['preisanpassung']); ?></p>
                        <p class="description"><?php echo esc_html($tarif['kurzbeschreibung']); ?></p>
                    </div>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
        <?php
        return ob_get_clean();
    }

    public function diagramm_shortcode($atts) {
        $atts = shortcode_atts(array(
            'type' => 'bar',
            'title' => 'Tarifübersicht'
        ), $atts);

        $tarife = $this->get_tarif_data(10);
        
        if (isset($tarife['error'])) {
            return '<div class="error-message">' . esc_html($tarife['error']) . '</div>';
        }

        // Chart.js einbinden
        wp_enqueue_script('chartjs', 'https://cdn.jsdelivr.net/npm/chart.js', array(), null, true);

        // Daten für das Diagramm aufbereiten
        $labels = array_map(function($tarif) {
            return $tarif['tarifname'];
        }, $tarife);

        // Eindeutige ID für das Canvas-Element
        $chart_id = 'chart_' . uniqid();

        ob_start();
        ?>
        <div class="chart-container">
            <canvas id="<?php echo esc_attr($chart_id); ?>"></canvas>
        </div>
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            var ctx = document.getElementById('<?php echo esc_js($chart_id); ?>').getContext('2d');
            new Chart(ctx, {
                type: '<?php echo esc_js($atts['type']); ?>',
                data: {
                    labels: <?php echo json_encode($labels); ?>,
                    datasets: [{
                        label: '<?php echo esc_js($atts['title']); ?>',
                        data: <?php echo json_encode(range(10, count($labels) * 10, 10)); ?>,
                        backgroundColor: 'rgba(46, 204, 113, 0.2)',
                        borderColor: 'rgba(46, 204, 113, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        });
        </script>
        <?php
        return ob_get_clean();
    }
}

// Plugin initialisieren
$strom_tarif_plugin = new StromTarifPlugin();

// Aktivierungshook
register_activation_hook(__FILE__, function() {
    // Stylesheet-Datei erstellen
    $css = "
    .stromtarife-table-container {
        overflow-x: auto;
        margin: 20px 0;
    }
    .stromtarife-table {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, sans-serif;
    }
    .stromtarife-table th,
    .stromtarife-table td {
        padding: 12px;
        border: 1px solid #ddd;
        text-align: left;
    }
    .stromtarife-table th {
        background-color: #f5f5f5;
        font-weight: bold;
    }
    .stromtarife-table tr:hover {
        background-color: #f9f9f9;
    }
    .stromtarife-cards {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 20px;
        margin: 20px 0;
    }
    .tarif-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .tarif-header {
        background-color: #f5f5f5;
        padding: 15px;
        border-bottom: 1px solid #ddd;
    }
    .tarif-header h3 {
        margin: 0;
        color: #333;
    }
    .tarif-header .anbieter {
        font-size: 0.9em;
        color: #666;
    }
    .tarif-body {
        padding: 15px;
    }
    .tarif-price {
        font-size: 1.4em;
        color: #2ecc71;
        margin-bottom: 15px;
    }
    .tarif-details p {
        margin: 5px 0;
    }
    .description {
        font-size: 0.9em;
        color: #666;
        margin-top: 10px;
    }
    .chart-container {
        height: 400px;
        margin: 20px 0;
    }
    .stromtarife-attribution {
    text-align: right;
    font-size: 0.8em;
    color: #666;
    margin-top: 10px;
}

.stromtarife-attribution a {
    color: #666;
    text-decoration: none;
}

.stromtarife-attribution a:hover {
    text-decoration: underline;
}

.error-message {
        padding: 10px;
        background-color: #ffe6e6;
        border: 1px solid #ff9999;
        color: #cc0000;
        border-radius: 4px;
        margin: 10px 0;
    }";

    // CSS-Datei im Plugin-Verzeichnis speichern
    $css_dir = plugin_dir_path(__FILE__) . 'css';
    if (!file_exists($css_dir)) {
        mkdir($css_dir, 0755, true);
    }
    file_put_contents($css_dir . '/style.css', $css);
});