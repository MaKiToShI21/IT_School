function confirmDelete() {
    const selectedId = document.getElementById('selected-item-id').value;
    if (selectedId) {
        return confirm('Вы уверены, что хотите удалить данную запись?');
    }
}