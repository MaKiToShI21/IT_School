document.addEventListener('DOMContentLoaded', function() {
    const sqlTemplates = document.getElementById('sql-templates');
    const sqlTextarea = document.querySelector('textarea[name="sql_request"]');
    
    sqlTemplates.addEventListener('change', function() {
        if (this.value) {
            sqlTextarea.value = this.value;
            sqlTextarea.focus();
        }
    });
});