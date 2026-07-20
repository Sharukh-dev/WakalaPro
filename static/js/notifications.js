document.addEventListener("DOMContentLoaded", function () {


    let currentCount = parseInt(
        document.getElementById("notification-count")?.innerText || 0
    );



    function checkNotifications() {


        fetch("/api/notifications/count")

        .then(response => response.json())

        .then(data => {


            let newCount = data.count;



            if (newCount > currentCount) {


                showNotificationAlert();


                playNotificationSound();


            }



            currentCount = newCount;


        })

        .catch(error => {

            console.log(error);

        });



    }





    function showNotificationAlert() {


        if (Notification.permission === "granted") {


            new Notification(
                "WakalaPro Alert",
                {
                    body:
                    "You have a new business notification."
                }
            );


        }


        else if(Notification.permission !== "denied"){


            Notification.requestPermission();


        }


    }





    function playNotificationSound(){


        let audio = new Audio(
            "/static/sounds/notification.mp3"
        );


        audio.play();



    }





    setInterval(
        checkNotifications,
        10000
    );



});