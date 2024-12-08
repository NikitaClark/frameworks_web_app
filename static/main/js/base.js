
    

    function showTooltip() {
        document.getElementById('tokenTooltip').style.display = 'block';
    }

    function hideTooltip() {
        document.getElementById('tokenTooltip').style.display = 'none';
    }

    window.onload = function() {
        var userIconButton = document.getElementById('user-icon-button');
        
        if (userIconButton) {
            userIconButton.addEventListener('click', function(event) {
                event.stopPropagation();
                var dropdownMenu = document.getElementById('dropdown-menu');
                dropdownMenu.style.display = (dropdownMenu.style.display === 'none' || dropdownMenu.style.display === '') ? 'block' : 'none';
            });

            window.onclick = function(event) {
                var dropdownMenu = document.getElementById('dropdown-menu');
                if (!event.target.matches('#user-icon-button') && !dropdownMenu.contains(event.target)) {
                    dropdownMenu.style.display = 'none';
                }
            };
        }
    };

    function myFunction() {
        const dropdown = document.getElementById("myDropdown");
        const button = document.querySelector(".dropbtn");

        if (dropdown) {
            dropdown.classList.toggle("show");

            if (dropdown.classList.contains("show")) {
                button.textContent = "Story -"; 
            } else {
                button.textContent = "Story +"; 
            }
        }
    }

    window.addEventListener('click', function(event) {
        const dropdown = document.getElementById("myDropdown");
        const button = document.querySelector(".dropbtn");

        if (dropdown) {

            if (!event.target.matches('.dropbtn') && !dropdown.contains(event.target)) {

                if (dropdown.classList.contains('show')) {
                    dropdown.classList.remove('show');

                    button.textContent = "Story +";
                }
            }
        }
    });

