<?php
/**
 * Plugin Name: Strom Tarif Plugin
 * Plugin URI: https://example.com/plugins/strom-tarif-plugin
 * Description: Displays electricity tariff information from API
 * Version: 1.0.0
 * Author: Your Name
 * License: GPL v2 or later
 * Text Domain: strom-tarif
 */

if (!defined('WPINC')) {
    die;
}

class Strom_Tarif_Plugin {
    private static $instance = null;
    private $cache_time = 3600; // 1 hour cache

    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        add_shortcode('display_strom_tariffs', array($this, 'display_tariffs_shortcode'));
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_init', array($this, 'register_settings'));
    }

    private function fetch_tariff_data($rows = 10) {
        // Check cache first
        $cache_key = 'strom_tariff_data_' . $rows;
        $cached_data = get_transient($cache_key);

        if ($cached_data !== false) {
            return $cached_data;
        }

         $api_url = 'https://amd1.mooo.com/api/electricity/tarifliste?rows=' . intval($rows) . '&contentformat=json';

        $response = wp_remote_get($api_url);
        
        if (is_wp_error($response)) {
            return array('error' => 'Failed to fetch data from API');
        }

        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            return array('error' => 'Failed to parse JSON response');
        }

        // Cache the data
        set_transient($cache_key, $data, $this->cache_time);

        return $data;
    }
    
     private function render_table_layout($data, $selected_provider = '') {
        if (isset($data['error'])) {
            return '<div class="error-message">' . esc_html($data['error']) . '</div>';
        }

        $output = '<div class="strom-tariffs">';
        $output .= '<h2>Strom Tariffs</h2>';
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

       foreach ($data as $tariff) {
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

         $output = '<div class="strom-tariffs">';
        $output .= '<h2>Strom Tariffs</h2>';
        $output .= '<div class="tariff-cards">';


        foreach ($data as $tariff) {
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
                'layout' => 'table', // Options: table, cards
                'rows'   => get_option('strom_tarif_table_rows', 10),      // Default number of rows
                'stromanbieter' => '', // New parameter for filtering by provider
            ),
            $atts,
            'display_strom_tariffs'
        );

        wp_enqueue_style('strom-tarif-styles', plugins_url('css/style.css', __FILE__));
        $selected_provider = get_option('strom_tarif_card_provider', '');
        $data = $this->fetch_tariff_data($atts['rows']);

         if ($atts['layout'] === 'cards') {
             return $this->render_cards_layout($data, $selected_provider, $atts['stromanbieter']);
         }
        
        return $this->render_table_layout($data, $atts['stromanbieter']);
    }
    
     public function register_settings() {
         // Table Rows Setting
        register_setting( 'strom_tarif_settings_group', 'strom_tarif_table_rows', array('sanitize_callback' => 'absint') );
        add_settings_section(
            'strom_tarif_table_settings',
            'Table Settings',
            array($this, 'table_settings_section_callback'),
            'strom-tariffs-settings-page'
        );
        add_settings_field(
            'strom_tarif_table_rows',
            'Default Table Rows',
            array($this, 'table_rows_field_callback'),
            'strom-tariffs-settings-page',
            'strom_tarif_table_settings'
        );
        
         // Card Provider Setting
        register_setting('strom_tarif_settings_group', 'strom_tarif_card_provider', array('sanitize_callback' => 'sanitize_text_field'));
          add_settings_section(
            'strom_tarif_card_settings',
            'Card Settings',
            array($this, 'card_settings_section_callback'),
            'strom-tariffs-settings-page'
        );
        add_settings_field(
            'strom_tarif_card_provider',
            'Select Provider for Cards',
            array($this, 'card_provider_field_callback'),
            'strom-tariffs-settings-page',
            'strom_tarif_card_settings'
        );
    }
    
    public function table_settings_section_callback() {
        echo '<p>Configure the default settings for the table layout.</p>';
    }
     public function card_settings_section_callback() {
        echo '<p>Configure the settings for the card layout.</p>';
    }
      public function table_rows_field_callback() {
        $rows = get_option('strom_tarif_table_rows', 10);
        echo '<input type="number" name="strom_tarif_table_rows" value="' . esc_attr($rows) . '" />';
    }
    public function card_provider_field_callback() {
        $selected_provider = get_option('strom_tarif_card_provider', '');
         $data = $this->fetch_tariff_data(100);
        if (isset($data['error'])){
           echo '<p>error</p>';
           return;
        }
        echo '<select name="strom_tarif_card_provider">';
        echo '<option value="" ' . selected($selected_provider, '', false) . '>All</option>';
         
           $providers = array_unique(array_column($data, 'stromanbieter'));
           foreach ($providers as $provider) {
              echo '<option value="' . esc_attr($provider) . '" ' . selected($selected_provider, $provider, false) . '>' . esc_html($provider) . '</option>';
            }
        echo '</select>';
     }

    public function add_admin_menu() {
         add_menu_page(
            'Strom Tariffs',
            'Strom Tariffs',
            'manage_options',
            'strom-tariffs',
            array($this, 'display_admin_page'),
            'dashicons-chart-bar',
            100
        );
           add_submenu_page(
            'strom-tariffs',
            'Strom Tarif Settings',
            'Settings',
            'manage_options',
            'strom-tariffs-settings-page',
            array($this, 'display_settings_page')
        );
    }
    
      public function display_settings_page() {
          echo '<div class="wrap">';
          echo '<h1>Strom Tarif Settings</h1>';
          echo '<form method="post" action="options.php">';
            settings_fields( 'strom_tarif_settings_group' );
            do_settings_sections( 'strom-tariffs-settings-page' );
            submit_button();
           echo '</form>';
           echo '</div>';
      }

      public function display_admin_page() {
        echo '<div class="wrap">';
        echo '<h1>Strom Tariffs</h1>';
        echo '<p>Use these shortcodes to display the tariff information:</p>';
        echo '<ul>';
        echo '<li><code>[display_strom_tariffs]</code> - Display as table (default from settings, default 10 rows)</li>';
        echo '<li><code>[display_strom_tariffs rows="5"]</code> - Display as table with 5 rows</li>';
         echo '<li><code>[display_strom_tariffs stromanbieter="oekostrom"]</code> - Display as table filtered for oekostrom (default rows)</li>';
        echo '<li><code>[display_strom_tariffs layout="cards"]</code> - Display as cards (default from settings, default all providers)</li>';
        echo '<li><code>[display_strom_tariffs layout="cards" rows="5"]</code> - Display as cards with 5 rows, (card provider setting still applies)</li>';
        echo '<li><code>[display_strom_tariffs layout="cards" stromanbieter="oekostrom"]</code> - Display as cards filtered for oekostrom (default settings)</li>';
        echo '</ul>';
        echo '<h2>Table Layout Preview</h2>';
        echo do_shortcode('[display_strom_tariffs]');
        echo '<h2>Table Layout Preview (5 rows)</h2>';
        echo do_shortcode('[display_strom_tariffs rows="5"]');
         echo '<h2>Table Layout Preview (oekostrom)</h2>';
        echo do_shortcode('[display_strom_tariffs stromanbieter="oekostrom"]');
        echo '<h2>Cards Layout Preview</h2>';
        echo do_shortcode('[display_strom_tariffs layout="cards"]');
        echo '<h2>Cards Layout Preview (5 rows)</h2>';
        echo do_shortcode('[display_strom_tariffs layout="cards" rows="5"]');
        echo '<h2>Cards Layout Preview (oekostrom)</h2>';
        echo do_shortcode('[display_strom_tariffs layout="cards" stromanbieter="oekostrom"]');
        echo '</div>';
    }
}

// Initialize the plugin
Strom_Tarif_Plugin::get_instance();
