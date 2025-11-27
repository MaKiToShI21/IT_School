function toggleRadio(radio) {
    const selectedItemInput = document.getElementById('selected-item-id');
    
    if (radio.checked && radio === document.activeRadio) {
        radio.checked = false;
        document.activeRadio = null;
        selectedItemInput.value = '';
    } else {
        document.activeRadio = radio.checked ? radio : null;
        if (radio.checked) {
            selectedItemInput.value = radio.value;
        }
    }
    
    updateButtonStates();
}

function updateButtonStates() {
    const selectedItemInput = document.getElementById('selected-item-id');
    const editButton = document.querySelector('button[value="edit"]');
    const deleteButton = document.querySelector('button[value="delete"]');
    
    const hasSelection = selectedItemInput && selectedItemInput.value !== '';
    
    if (editButton) editButton.disabled = !hasSelection;
    if (deleteButton) deleteButton.disabled = !hasSelection;
}

document.addEventListener('DOMContentLoaded', updateButtonStates);