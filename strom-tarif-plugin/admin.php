<?php
/**
 * Admin Panel for Strom Tarif Plugin.
 *
 * This file contains only the description of shortcodes.
 *
 * Available Shortcodes:
 * - [strom_tariff]: Renders the tariff information.
 * - [another_shortcode]: Description.
 */

require_once plugin_dir_path(__FILE__) . 'developer.php'; // Include developer settings

class Strom_Tarif_Admin {

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
        // New Developer subpage
        add_submenu_page(
            'strom-tariffs',
            'Strom Tarif Developer Settings',
            'Developer',
            'manage_options',
            'strom-tariffs-developer-page',
            'strom_tarif_developer_settings_page'
        );
    }

    public function display_admin_page() {
        echo '<div class="wrap">';
        echo '<h1>Strom Tariffs</h1>';
        echo '<p>Use these shortcodes to display the tariff information:</p>';
        echo '<ul>';
        echo '<li><code>[display_strom_tariffs]</code> - Display as table (default from settings, default 10 rows)</li>';
        echo '<li><code>[display_strom_tariffs rows="5"]</code> - Display as table with 5 rows</li>';
        echo '<li><code>[display_strom_tariffs layout="cards"]</code> - Display as cards (default from settings, default all providers)</li>';
        echo '<li><code>[display_strom_tariffs layout="cards" rows="5"]</code> - Display as cards with 5 rows (card provider setting still applies)</li>';
        echo '</ul>';
        echo '</div>';
    }

    public function display_settings_page() {
        echo '<div class="wrap">';
        echo '<h1>Strom Tarif Settings</h1>';
        echo '<form method="post" action="options.php">';
        settings_fields('strom_tarif_settings_group');
        do_settings_sections('strom-tariffs-settings-page');
        submit_button();
        echo '</form>';
        echo '</div>';
    }
}


//Register settings
add_action('admin_init', 'strom_tarif_register_settings');
function strom_tarif_register_settings() {
    // API Key Setting
    register_setting('strom_tarif_settings_group', 'strom_tarif_api_key', array('sanitize_callback' => 'sanitize_text_field'));
    add_settings_section(
        'strom_tarif_api_settings',
        'API Settings',
        'strom_tarif_api_settings_section_callback',
        'strom-tariffs-settings-page'
    );
    add_settings_field(
        'strom_tarif_api_key',
        'API Key',
        'strom_tarif_api_key_field_callback',
        'strom-tariffs-settings-page',
        'strom_tarif_api_settings'
    );

    // Table Rows Setting
    register_setting('strom_tarif_settings_group', 'strom_tarif_table_rows', array('sanitize_callback' => 'absint'));
    add_settings_section(
        'strom_tarif_table_settings',
        'Table Settings',
        'strom_tarif_table_settings_section_callback',
        'strom-tariffs-settings-page'
    );
    add_settings_field(
        'strom_tarif_table_rows',
        'Default Table Rows',
        'strom_tarif_table_rows_field_callback',
        'strom-tariffs-settings-page',
        'strom_tarif_table_settings'
    );

    // Card Provider Setting
    register_setting('strom_tarif_settings_group', 'strom_tarif_card_provider', array('sanitize_callback' => 'sanitize_text_field'));
    add_settings_section(
        'strom_tarif_card_settings',
        'Card Settings',
        'strom_tarif_card_settings_section_callback',
        'strom-tariffs-settings-page'
    );
    add_settings_field(
        'strom_tarif_card_provider',
        'Select Provider for Cards',
//        'strom_tarif_card_provider_field_callback',
        'strom-tariffs-settings-page',
        'strom_tarif_card_settings'
    );
}

function strom_tarif_api_settings_section_callback() {
    echo '<p>Enter your API key to access the data.</p>';
}

function strom_tarif_api_key_field_callback() {
    $api_key = get_option('strom_tarif_api_key');
    echo '<input type="text" name="strom_tarif_api_key" value="' . esc_attr($api_key) . '" size="40" />';
}

function strom_tarif_table_settings_section_callback() {
    echo '<p>Configure the default settings for the table layout.</p>';
}

function strom_tarif_card_settings_section_callback() {
    echo '<p>Configure the settings for the card layout.</p>';
}

function strom_tarif_table_rows_field_callback() {
    $rows = get_option('strom_tarif_table_rows', 10);
    echo '<input type="number" name="strom_tarif_table_rows" value="' . esc_attr($rows) . '" />';
}



// Add admin menu
add_action('admin_menu', array(new Strom_Tarif_Admin(), 'add_admin_menu'));
