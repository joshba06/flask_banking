document.addEventListener("DOMContentLoaded", () => {
  console.log("Hello from autocomplete file");
  $("#autocomplete").autocomplete({
      source: unique_titles
  });
});
