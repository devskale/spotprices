<?php
/**
 * Developer Settings Page for Strom Tarif Plugin
 */

// Replace the settings page callback to use a unique settings group:
function strom_tarif_developer_settings_page() {
    echo '<div class="wrap">';
    echo '<h1>Developer Settings</h1>';
    echo '<form method="post" action="options.php">';
    settings_fields('strom_tarif_developer_settings_group'); // Use unique group here
    do_settings_sections('strom-tariffs-developer-page');
    submit_button();
    echo '</form>';
    echo '</div>';
}

function strom_tarif_developer_settings_init() {
    register_setting(
        'strom_tarif_developer_settings_group', // Use unique group here
        'strom_tarif_api_url',
        array('sanitize_callback' => 'esc_url_raw')
    );

    add_settings_section(
        'developer_api_settings_section', // ID
        'API URL Settings',               // Title
        'strom_tarif_developer_api_section_info', // Callback
        'strom-tariffs-developer-page'    // Page slug
    );

    add_settings_field(
        'strom_tarif_api_url',            // Field ID
        'API URL',                        // Title
        'strom_tarif_api_url_field_callback', // Callback
        'strom-tariffs-developer-page',   // Page slug
        'developer_api_settings_section'  // Section ID
    );
}

function strom_tarif_developer_api_section_info() {
    echo '<p>Enter the API URL to use for development purposes. Use with caution!</p>';
}

function strom_tarif_api_url_field_callback() {
    $api_url = get_option('strom_tarif_api_url', 'https://amd1.mooo.com/api/'); // Default API URL
    printf(
        '<input type="url" id="strom_tarif_api_url" name="strom_tarif_api_url" value="%s" size="80" />',
        esc_url_raw($api_url) // Sanitize the output
    );
}

// Hook the settings initialization
add_action('admin_init', 'strom_tarif_developer_settings_init');
// Add the developer settings page to the admin menu
add_action('admin_menu', function() {
    add_submenu_page(
        'strom-tariffs',
        'Strom Tarif Developer Settings',
        'Developer',
        'manage_options',
        'strom-tariffs-developer-page',
        'strom_tarif_developer_settings_page'
    );
});
