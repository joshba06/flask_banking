document.addEventListener("DOMContentLoaded", function() {
  const addTransactionButton = document.getElementById("btn-add-transaction");
  const cancelAddingTransactionButton = document.getElementById("btn-cancel-add-transaction");
  const newTransactionForm = document.getElementById("new-transaction");

  // Add click event listener to "Add Transaction" button
  addTransactionButton.addEventListener("click", function(event) {
      event.preventDefault();
      addTransactionButton.style.display = "none";
      cancelAddingTransactionButton.style.display = "inline";
      newTransactionForm.style.display = "flex";
      newTransactionForm.classList.add("form-new-transaction")
      // newTransactionForm.style.justifyContent = "space-around";
  });

  // Add click event listener to "Cancel" button
  cancelAddingTransactionButton.addEventListener("click", function(event) {
      event.preventDefault();
      addTransactionButton.style.display = "block";
      cancelAddingTransactionButton.style.display = "none";
      newTransactionForm.style.display = "none";
  });
});
