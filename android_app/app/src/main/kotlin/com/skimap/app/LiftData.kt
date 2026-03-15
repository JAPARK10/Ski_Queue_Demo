package com.skimap.app

/**
 * Represents a single ski lift on the map.
 *
 * @param id               Short identifier shown on the map (e.g. "G")
 * @param name             Human-readable lift name
 * @param xPct             Horizontal position as % of map image width  (0..100)
 * @param yPct             Vertical   position as % of map image height (0..100)
 * @param videoAsset       Filename inside assets/videos/ (e.g. "lift_G_counted.mp4")
 * @param countsPerSecond  Per-second queue counts from batch_count_videos.py (looping)
 */
data class LiftData(
    val id: String,
    val name: String,
    val xPct: Float,
    val yPct: Float,
    val videoAsset: String,
    val countsPerSecond: List<Int>
) {
    /** Returns the live count for the given elapsed seconds (wraps around the list). */
    fun currentCount(elapsedSeconds: Long): Int {
        if (countsPerSecond.isEmpty()) return 0
        val idx = (elapsedSeconds % countsPerSecond.size).toInt()
        return countsPerSecond[idx]
    }
}
