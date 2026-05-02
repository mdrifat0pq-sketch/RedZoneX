// আপনার গুগল ড্রাইভের ভিডিও লিস্ট এখানে যুক্ত করুন
const videoData = [
    {
        title: "Exclusive Video 1",
        url: "https://drive.google.com/file/d/17IhpcTwZYo25p1m5d3L0YGkUln-s5p4M/view?usp=drivesdk",
        thumbnail: "https://i.ibb.co.com/zVV26Bht/image-16.jpg" // এখানে আপনি আলাদা থাম্বনেইলও দিতে পারেন
    }
    // ভবিষ্যতে আরও ভিডিও এখানে যোগ করতে পারবেন
];

const videoGrid = document.getElementById('video-grid');

// গুগল ড্রাইভ লিঙ্ককে ডিরেক্ট প্লে লিঙ্কে রূপান্তর করার ফাংশন
function getDirectLink(url) {
    const fileId = url.split('/d/')[1].split('/')[0];
    return `https://drive.google.com/uc?export=download&id=${fileId}`;
}

// ভিডিও কার্ডগুলো অ্যাপে দেখানোর ফাংশন
function loadVideos() {
    videoGrid.innerHTML = ''; // লোডিং টেক্সট মুছে ফেলা

    videoData.forEach((video, index) => {
        const directLink = getDirectLink(video.url);
        
        const card = document.createElement('div');
        card.className = 'video-card';
        card.innerHTML = `
            <div class="thumbnail" onclick="playVideo('${directLink}')" style="background-image: url('${video.thumbnail}'); background-size: cover; height: 110px; position: relative; border-radius: 8px; cursor: pointer;">
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: white; font-size: 30px;">▶</div>
            </div>
            <div class="video-info" style="padding: 10px 0;">
                <p style="font-size: 14px; color: #fff;">${video.title}</p>
            </div>
        `;
        videoGrid.appendChild(card);
    });
}

// ভিডিও প্লে করার ফাংশন
function playVideo(link) {
    // টেলিগ্রামে বা ব্রাউজারে ভিডিও প্লে করার সহজ উপায়
    window.open(link, '_blank');
}

// অ্যাপ লোড হলে ভিডিও দেখাবে
window.onload = loadVideos;
