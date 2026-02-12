<?php
/**
 * Simple PHP Templating System
 * Provides basic template rendering with variable substitution
 */

class Template {
    private $vars = [];
    private $template_dir = __DIR__ . '/templates/';

    public function __construct($template_dir = null) {
        if ($template_dir) {
            $this->template_dir = $template_dir;
        }
    }

    public function set($key, $value) {
        $this->vars[$key] = $value;
        return $this;
    }

    public function setMultiple($array) {
        $this->vars = array_merge($this->vars, $array);
        return $this;
    }

    public function render($template_file) {
        $template_path = $this->template_dir . $template_file;

        if (!file_exists($template_path)) {
            throw new Exception("Template file not found: $template_path");
        }

        // Extract variables to local scope
        extract($this->vars);

        // Start output buffering
        ob_start();

        // Include the template
        include $template_path;

        // Get the rendered content
        $content = ob_get_clean();

        return $content;
    }

    public function display($template_file) {
        echo $this->render($template_file);
    }

    // Helper method for common page variables
    public function setPageData($title = '', $data = []) {
        $defaults = [
            'page_title' => $title ?: 'Phil Collins Detector',
            'current_year' => date('Y'),
            'base_url' => '/'
        ];

        return $this->setMultiple(array_merge($defaults, $data));
    }
}

// Global template instance
$template = new Template(__DIR__ . '/templates/');
?>