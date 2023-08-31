document.addEventListener('DOMContentLoaded', function() {
  const sortButton = document.getElementById('sortButton');
  const transactionsTable = document.getElementById('transactionsTable');
  const tbody = transactionsTable.querySelector('tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  let ascending = true;

  sortButton.addEventListener('click', function() {
      ascending = !ascending;
      sortButton.textContent = ascending ? 'Descending' : 'Ascending';

      const sortedRows = rows.slice().sort(function(rowA, rowB) {
          const dateA = new Date(rowA.cells[0].textContent);
          const dateB = new Date(rowB.cells[0].textContent);
          return ascending ? dateA - dateB : dateB - dateA;
      });

      tbody.innerHTML = '';
      sortedRows.forEach(function(row) {
          tbody.appendChild(row);
      });
      console.log(sortedRows)
  });
});
