package com.skimap.app

import android.content.Context
import com.google.gson.Gson
import com.google.gson.annotations.SerializedName

// ──────────────────────────────────────────────────────────────
// JSON structure that mirrors people_counts.json
// ──────────────────────────────────────────────────────────────
private data class JsonRoot(val lifts: List<JsonLift>)

private data class JsonLift(
    val id: String,
    val name: String,
    @SerializedName("x_pct") val xPct: Float,
    @SerializedName("y_pct") val yPct: Float,
    val video: String,
    @SerializedName("counts_per_second") val countsPerSecond: List<Int>
)

// ──────────────────────────────────────────────────────────────
// Repository
// ──────────────────────────────────────────────────────────────
object LiftRepository {

    /**
     * Load lift data from assets/videos/people_counts.json.
     * Falls back to hardcoded defaults if the file is missing.
     */
    fun load(context: Context): List<LiftData> {
        return try {
            val json = context.assets
                .open("videos/people_counts.json")
                .bufferedReader()
                .readText()
            val root = Gson().fromJson(json, JsonRoot::class.java)
            root.lifts.map { j ->
                LiftData(
                    id               = j.id,
                    name             = j.name,
                    xPct             = j.xPct,
                    yPct             = j.yPct,
                    videoAsset       = j.video,
                    countsPerSecond  = j.countsPerSecond.ifEmpty { listOf(0) }
                )
            }
        } catch (e: Exception) {
            fallbackLifts()
        }
    }

    /** Hardcoded fallback — short sample sequences so the app still animates without JSON. */
    private fun fallbackLifts(): List<LiftData> = listOf(
        LiftData("G", "Kings Cab",         2.5f,  61.0f, "lift_G_counted.mp4", listOf(2,3,3,4,3,2)),
        LiftData("C", "Tiergartenalm",    14.0f,  57.0f, "lift_C_counted.mp4", listOf(7,8,9,8,7,8)),
        LiftData("E", "Tiergartenbahn",   21.0f,  55.0f, "lift_E_counted.mp4", listOf(13,14,15,14,13)),
        LiftData("J", "Zachhofalmbahn",   40.0f,  69.0f, "lift_J_counted.mp4", listOf(4,5,5,4,5)),
        LiftData("K", "Bürglalmbahn",     44.0f,  69.0f, "lift_K_counted.mp4", listOf(10,11,12,11,10)),
        LiftData("L", "Wastlhöhelift",    41.0f,  51.0f, "lift_L_counted.mp4", listOf(1,2,2,1,2)),
        LiftData("I", "Liebenauslm",      50.0f,  62.0f, "lift_I_counted.mp4", listOf(6,7,8,7,6)),
        LiftData("M", "Gabühelbahn",      57.0f,  63.0f, "lift_M_counted.mp4", listOf(14,16,17,16,15)),
        LiftData("N", "Steinbockalmbahn", 66.0f,  64.0f, "lift_N_counted.mp4", listOf(8,9,10,9,8))
    )
}
