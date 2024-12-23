function alert(title, message) {
    return  `
        <!-- The Modal -->
        <div class="modal fade" id="myModal" tabindex="-1" role="dialog" aria-hidden="true">
          <div class="modal-dialog" role="document">
            <div class="modal-content">

              <!-- Modal Header -->
              <div class="modal-header">
                <h4 class="modal-title">${title}</h4>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>

              <!-- Modal body -->
              <div class="modal-body">
                ${message}
              </div>

              <!-- Modal footer -->
              <div class="modal-footer">
                <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Close</button>
              </div>

            </div>
          </div>
        </div>`
}

function validateDataDate(event, checkin, checkout) {
    event.preventDefault();
    console.log("2")
    if (checkin && checkout) {
        console.log("1")
        let checkinDate = new Date(checkin);
        let checkoutDate = new Date(checkout);

        if (checkinDate > checkoutDate) {
            console.log("2")
            let popup = document.querySelector('.popup');
            popup.innerHTML = alert("Alert", "Please fill in both check-in and check-out dates.");
            var myModal = new bootstrap.Modal(document.getElementById('myModal'));
            myModal.show();
        } else {
            event.target.submit();
        }
    }
}

function loginRequired() {
    let popup = document.querySelector(".popup")
    popup.innerHTML = `
        <!-- The Modal -->
        <div class="modal fade" id="myModal" tabindex="-1" role="dialog" aria-hidden="true">
          <div class="modal-dialog" role="document">
            <div class="modal-content">

              <!-- Modal Header -->
              <div class="modal-header">
                <h4 class="modal-title">Please Login</h4>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>

              <!-- Modal body -->
              <div class="modal-body">
                You must be logged in to book your hotel.
              </div>

              <!-- Modal footer -->
              <div class="modal-footer">
                <button type="button" class="btn btn-primary" data-bs-dismiss="modal">
                    <a href="/login" class="text-white">Login</a>
                </button>
                <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Close</button>
              </div>

            </div>
          </div>
        </div>`
    var myModal = new bootstrap.Modal(document.getElementById('myModal'));
    myModal.show();
}

function checkRoomAvailability(roomId) {
    let checkin = document.getElementById('check-in').value;
    let checkout = document.getElementById('check-out').value;
    let popup = document.querySelector(".popup")



    if (!checkin || !checkout) {
        popup.innerHTML = alert("Alert", "Please fill in both check-in and check-out dates.");
        var myModal = new bootstrap.Modal(document.getElementById('myModal'));
        myModal.show();
        return;
    }

    fetch('/api/check_room_availability', {
        method: 'POST',
        body: JSON.stringify({
            'room_id': roomId,
            'checkin': checkin,
            'checkout': checkout
        }),
        headers: {'Content-Type': 'application/json'}
    }).then(res => res.json()).then(data => {
        if (data.isAvailable) {
            window.location.href = `/booking/?room_id=${roomId}`;
        } else {
            popup.innerHTML = alert('Please choose another room.', 'The room has been booked or rented.')
            var myModal = new bootstrap.Modal(document.getElementById('myModal'));
            myModal.show();
        }
    })
}

let count = 1;

function addCustomer() {
    if (count <= 2) {
        count += 1
        let customer = document.querySelector(".list-customer");
        customer.insertAdjacentHTML("beforeend", `
        <div class="col-md-6 mb-3 customer-item">
            <div class="p-3 customer-update" style="background: #D9D9D9;">
                <div class="row">
                    <h6 class="col-md-9"">Customer ${count}:</h6>
                    <button type="button" class="btn btn-danger col-md-3 delete-customer">Delete</button>
                </div>
                <div class="mb-2">
                    <label for="name" class="form-label">Name:</label>
                    <input type="text" id="name${count}" class="form-control name" name="name" required>
                </div>
                <div class="mb-2">
                    <label for="id" class="form-label">Identification number:</label>
                    <input type="text" id="id${count}" class="form-control id" name="identification_card" required>
                    <p class="text-danger" style="display: none; font-style: italic"></p>
                </div>
                <div style="text-align: left">
                    <p>Chosse Customer Type</p>
                    <select id="type${count}" class="form-select rounded-0  customer_type" name="customer_type"
                            style="height: 40px;">
                        <option value="Domestic">Domestic</option>
                        <option value="Foreign">Foreign</option>
                    </select>
                </div>
            </div>
        </div>
        `)
    } else {
        let info = document.querySelector(".info")
        info.style.display = "block";
    }
}

//======================Delete Customer==================================
let deleteCustomer = document.querySelector(".list-customer");

deleteCustomer.addEventListener("click", function (event) {
    if (event.target.classList.contains("delete-customer")) {
        event.target.closest(".customer-item").remove();
        count--;
        updateCustomer();
    }
});

//======================End Delete Customer==================================

function updateCustomer() {
    let listCustomer = document.querySelectorAll(".customer-item")
    listCustomer.forEach((item, index) => {
        if (index > 0) {//Bỏ customer đầu mặc định đã đăng kí tài khoản
            let customerNumber = index + 1;
            item.querySelector(".row > h6").textContent = `Customer ${customerNumber}`;
        }
    })
}

//============================================================================

window.onload = function () {
    let checkin = document.getElementById("check-in")
    let checkout = document.getElementById("check-out")
    checkin.addEventListener("change", saveDate)
    checkout.addEventListener("change", saveDate)

    function saveDate() {
        checkin = document.getElementById("check-in");
        checkout = document.getElementById("check-out");
        console.log(checkin.value);
        console.log(checkout.value);

        navigator.sendBeacon("/save_date", JSON.stringify({
            checkin: checkin.value,
            checkout: checkout.value,
        }))
    }
}

//==================================Auto Fill====================================
function autoFill(name, identification_card, customer_type) {
    let checked = document.querySelector(".cb")

    let nameCus = document.getElementById("name");
    let id = document.getElementById("id");
    let type = document.getElementById("type");

    if (!checked.checked) {
        nameCus.value = name;
        nameCus.readOnly = true;

        id.value = identification_card;
        id.readOnly = true;

        type.innerHTML = `<option value="${customer_type}">${customer_type}</option>`;
    } else {
        nameCus.value = '';
        nameCus.readOnly = false;

        id.value = '';
        id.readOnly = false;

        type.innerHTML = `<option value="Domestic">Domestic</option>
                            <option value="Foreign">Foreign</option>`;
    }
}

//===============================Validate CCCD====================================
function validate(event, roomId) {
    event.preventDefault();
    let valid = true;
    let inputId = document.querySelectorAll("input[name='identification_card']");
    let listId = [];

    let error = document.querySelector('.error')

    let arrayId = []

    for (let i = 0; i < inputId.length; i++) {
        let value = inputId[i].value.trim();
        if (value && arrayId.includes(value)) {
            console.log('sai');
            error.style.display = "block";
            valid = false;
            break;
        } else {
            error.style.display = "none";
            arrayId.push(value)
            valid = true;
        }
    }

    if (valid) {
        inputId.forEach(input => {
            const errorMessage = input.nextElementSibling;
            if (/^\d{12}$/.test(input.value) || /^\d{9}$/.test(input.value) || /^[a-zA-Z][a-zA-Z0-9]{7}$/.test(input.value)) {
                errorMessage.style.display = "none";
                listId.push(input.value);
                valid = true;
            } else {
                errorMessage.textContent = "Identification card is invalid.";
                errorMessage.style.display = "block";
                valid = false;
            }
        })

        if (valid) {
            let inputName = document.querySelectorAll("input[name='name']");
            let inputCustomerType = document.querySelectorAll(".customer_type");

            let listName = Array.from(inputName).map((item) => item.value.trim());
            let listCustomerType = Array.from(inputCustomerType).map((item) => item.value.trim());

            let checkin = document.getElementById("checkin").value;
            let checkout = document.getElementById("checkout").value;

            fetch('/api/check_account', {
                method: 'POST',
                body: JSON.stringify({
                    "listName": listName,
                    "listId": listId,
                    "listCustomerType": listCustomerType,
                    "checkin": checkin,
                    "checkout": checkout,
                    "roomId": roomId,
                }),
                headers: {
                    'Content-Type': 'application/json',
                }
            }).then(res => res.json()).then(data => {
                if (data.success) {
                    window.location.pathname = '/reservation';
                } else {
                    let popup = document.querySelector('.popup')
                    popup.innerHTML = alert('Regulation',
                        'When booking a room, the information of a person who has already registered an account in the system must be entered.')
                    var myModal = new bootstrap.Modal(document.getElementById('myModal'));
                    myModal.show();
                }
            })
        }
    }
}