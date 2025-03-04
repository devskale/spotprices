<?php
/**
 * Plugin Name: Strom Tarif Plugin
 * Plugin URI: https://skale.dev/plugins/strom-tarif-plugin
 * Description: Displays electricity tariff information from API.
 * Version:     1.0.5
 * Author:      dev@skale.dev
 * License:     GPL v2 or later
 * Text Domain: strom-tarif
 */

defined( 'ABSPATH' ) or die( 'No script kiddies please!' );

require_once plugin_dir_path(__FILE__) . 'admin.php'; // Include admin.php

class Strom_Tarif_Plugin {
    private static $instance = null;
    private $cache_time = 1; // 1 hour cache

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        add_shortcode('display_strom_tariffs', array($this, 'display_tariffs_shortcode'));
        add_shortcode('stromgraph', array($this, 'display_graph_shortcode'));
    }

    private function get_api_headers() {
        $api_key = get_option('strom_tarif_api_key', '');
        $headers = [];
        if (!empty($api_key)) {
            $headers['Authorization'] = 'Bearer ' . $api_key;
        }
        return $headers;
    }

    private function fetch_api_data($url) {
        $response = wp_remote_get($url, ['headers' => $this->get_api_headers()]);

        if (is_wp_error($response)) {
            error_log("API request failed: " . $response->get_error_message()); // Log the error for debugging
            return ['error' => 'Failed to fetch data from API'];
        }

        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            error_log("JSON decode failed: " . json_last_error_msg());
            return ['error' => 'Failed to parse JSON response'];
        }

        return $data;
    }

    private function fetch_graph_data($range = 'singleday') {
        // Check cache first
        $cache_key = 'strom_graph_data_' . $range;
        $cached_data = get_transient($cache_key);
    
        if ($cached_data !== false) {
            return $cached_data;
        }
        
        $base_url = get_option('strom_tarif_api_url', 'https://amd1.mooo.com/api'); 
        $api_url = $base_url . '/electricity/spotprices/chart/latest?range=' . urlencode($range);
        
        $args = array(
            'headers' => $this->get_api_headers(),
        );
        
        $response = wp_remote_get($api_url, $args);
        
        if (is_wp_error($response)) {
            return array('error' => 'Failed to fetch graph from API');
        }
    
        $body = wp_remote_retrieve_body($response);
        
        // Cache the SVG data
        set_transient($cache_key, $body, $this->cache_time);
        
        return $body;
    }

    public function display_graph_shortcode($atts) {
        $atts = shortcode_atts(
            array(
                'range' => 'singleday', // Default to single day view
            ),
            $atts,
            'stromgraph'
        );

        // Validate range parameter
        $valid_ranges = array('singleday', 'range');
        $range = in_array($atts['range'], $valid_ranges) ? $atts['range'] : 'singleday';

        $graph_data = $this->fetch_graph_data($range);
        
        if (is_array($graph_data) && isset($graph_data['error'])) {
            return '<div class="error-message">' . esc_html($graph_data['error']) . '</div>';
        }
    
        // Remove width and height attributes from SVG, add viewBox
        $graph_data = str_replace('<svg width="800" height="400"', '<svg viewBox="0 0 800 400"', $graph_data);
    
        $output = '<div class="strom-graph">';
        $output .= $graph_data; // SVG is already sanitized by WordPress
        $output .= $this->render_attribution();
        $output .= '</div>';
    
        return $output;
    }
    
    private function fetch_tariff_data($rows = 10) {
        $cache_key = 'strom_tariff_data_' . $rows;
        $cached_data = get_transient($cache_key);
        if ($cached_data !== false) {
            return $cached_data;
        }

        // Retrieve the base URL from developer settings:
        $base_url = get_option('strom_tarif_api_url', 'https://amd1.mooo.com/api'); 
        // Then construct the full URL:
        $api_url = $base_url . '/electricity/tarifliste?rows=' . intval($rows) . '&contentformat=json';
        $data = $this->fetch_api_data($api_url);
        set_transient($cache_key, $data, $this->cache_time);
        return $data;
    }

    private function render_table_layout($data, $selected_provider = '') {
        if (isset($data['error'])) {
            return '<div class="error-message">' . esc_html($data['error']) . '</div>';
        }

        // Handle both old and new API response formats
        $tariffs = isset($data['tariffs']) ? $data['tariffs'] : $data;
        $metadata = isset($data['metadata']) ? $data['metadata'] : null;

        $output = '<div class="strom-tariffs">';
        $output .= '<h2>Strom Tarife</h2>';
        
        // Display report date if available
        if ($metadata && isset($metadata['report_date'])) {
            $date = date_i18n(get_option('date_format'), strtotime($metadata['report_date']));
            $output .= '<p class="tariff-date">Stand: ' . esc_html($date) . '</p>';
        }
        
        $output .= '<table class="tariff-table">';
        $output .= '<thead><tr>';
        
        // Custom headers
        $headers = array(
            'provider_tariff' => array('Anbieter', 'Tarif'),
            'tarif_type' => array('Tarifart', 'Preisanpassung'),
            'strompreis' => 'Strompreis',
            'kurzbeschreibung' => 'Beschreibung'
        );
        
        foreach ($headers as $header) {
            if (is_array($header)) {
                $output .= '<th class="two-line-header">';
                $output .= '<div class="primary-text">' . esc_html($header[0]) . '</div>';
                $output .= '<div class="secondary-text">' . esc_html($header[1]) . '</div>';
                $output .= '</th>';
            } else {
                $output .= '<th>' . esc_html($header) . '</th>';
            }
        }
        
        $output .= '</tr></thead><tbody>';

       foreach ($tariffs as $tariff) {
            if (empty($selected_provider) || $tariff['stromanbieter'] === $selected_provider) {
              $output .= '<tr>';
            
              // Provider and Tariff Name combined
              $output .= '<td class="two-line-cell">';
              $output .= '<div class="primary-text">' . esc_html($tariff['stromanbieter']) . '</div>';
              $output .= '<div class="secondary-text">' . esc_html($tariff['tarifname']) . '</div>';
              $output .= '</td>';
            
              // Tarif Type and Price Adjustment combined
              $output .= '<td class="two-line-cell">';
              $output .= '<div class="primary-text">' . esc_html($tariff['tarifart']) . '</div>';
              $output .= '<div class="secondary-text">' . esc_html($tariff['preisanpassung']) . '</div>';
              $output .= '</td>';
            
              $output .= '<td>' . esc_html($tariff['strompreis']) . '</td>';
              $output .= '<td>' . esc_html($tariff['kurzbeschreibung']) . '</td>';
            
            $output .= '</tr>';
            }
        }
        $output .= '</tbody></table>';
        $output .= $this->render_attribution();
        $output .= '</div>';
        return $output;
    }
    
    private function render_cards_layout($data, $selected_provider = '', $shortcode_provider = '') {
        if (isset($data['error'])) {
            return '<div class="error-message">' . esc_html($data['error']) . '</div>';
        }

        // Handle both old and new API response formats
        $tariffs = isset($data['tariffs']) ? $data['tariffs'] : $data;
        $metadata = isset($data['metadata']) ? $data['metadata'] : null;

        $output = '<div class="strom-tariffs">';
        $output .= '<h2>Strom Tariffs</h2>';
        
        // Display report date if available
        if ($metadata && isset($metadata['report_date'])) {
            $date = date_i18n(get_option('date_format'), strtotime($metadata['report_date']));
            $output .= '<p class="tariff-date">Stand: ' . esc_html($date) . '</p>';
        }
        
        $output .= '<div class="tariff-cards">';

        foreach ($tariffs as $tariff) {
            $provider_match = empty($shortcode_provider) ? (empty($selected_provider) || $tariff['stromanbieter'] === $selected_provider) : ($tariff['stromanbieter'] === $shortcode_provider);
            if ($provider_match) {
                $output .= '<div class="tariff-card">';
            
                // Card Header
                $output .= '<div class="tariff-card-header">';
                $output .= '<div class="provider">' . esc_html($tariff['stromanbieter']) . '</div>';
                $output .= '<div class="tariff-name">' . esc_html($tariff['tarifname']) . '</div>';
                $output .= '</div>';

                // Card Body
                $output .= '<div class="tariff-card-body">';
            
                // Price Section
                $output .= '<div class="tariff-price">' . esc_html($tariff['strompreis']) . '</div>';
            
                // Details Section
                $output .= '<div class="tariff-details">';
                $output .= '<div class="tariff-type">';
                $output .= '<strong>' . esc_html($tariff['tarifart']) . '</strong><br>';
                $output .= '<span class="adjustment">' . esc_html($tariff['preisanpassung']) . '</span>';
                $output .= '</div>';
            
                $output .= '<div class="tariff-description">';
                $output .= esc_html($tariff['kurzbeschreibung']);
                $output .= '</div>';
            
                $output .= '</div>'; // End details
                $output .= '</div>'; // End card body
                $output .= '</div>'; // End card
             }
        }


        $output .= '</div>'; // End cards container
         $output .= $this->render_attribution();
        $output .= '</div>'; // End strom-tariffs
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
    public function display_tariffs_shortcode($atts) {
        $atts = shortcode_atts(
            array(
                'layout' => 'table',
                'rows'   => absint(get_option('strom_tarif_table_rows', 10)),
                'stromanbieter' => '',
            ),
            $atts,
            'display_strom_tariffs'
        );

        if ($atts['rows'] <= 0) {
            return '<div class="error-message">Invalid number of rows.</div>';
        }

        wp_enqueue_style('strom-tarif-styles', plugins_url('css/style.css', __FILE__));
        $selected_provider = get_option('strom_tarif_card_provider', '');
        $data = $this->fetch_tariff_data($atts['rows']);

        if ($atts['layout'] === 'cards') {
            return $this->render_cards_layout($data, $selected_provider, $atts['stromanbieter']);
        }

        return $this->render_table_layout($data, $atts['stromanbieter']);
    }
}

Strom_Tarif_Plugin::get_instance();
