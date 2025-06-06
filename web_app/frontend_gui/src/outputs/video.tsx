import styles from "./video.module.css"

export const VideoStream = () => {
    return (
        <>
            <h2>Video Stream</h2>
            <img className={styles.video} src="http://localhost:6543/api/video_feed" />
        </>
    )
}
