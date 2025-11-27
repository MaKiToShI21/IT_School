document.addEventListener('DOMContentLoaded', function() {
    const sqlTemplates = document.getElementById('sql-templates');
    const sqlTextarea = document.querySelector('textarea[name="sql_request"]');
    
    if (sqlTemplates === null)
        return;

    sqlTemplates.addEventListener('change', function() {
        if (this.value) {
            sqlTextarea.value = this.value;
            sqlTextarea.focus();
        }
    });
});