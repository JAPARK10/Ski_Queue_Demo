package com.skimap.app

import android.graphics.Color
import android.graphics.RectF
import android.graphics.Typeface
import android.graphics.drawable.LayerDrawable
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.TextView
import androidx.fragment.app.Fragment
import com.skimap.app.databinding.FragmentMapBinding

class MapFragment : Fragment() {

    private var _binding: FragmentMapBinding? = null
    private val binding get() = _binding!!

    private val handler = Handler(Looper.getMainLooper())
    private var startTimeMs = 0L

    // Map of LiftData to its Marker TextView
    private val liftMarkers = mutableMapOf<LiftData, TextView>()
    private val markerSizePx by lazy { dpToPx(44f) }
    private val circleSizePx by lazy { dpToPx(44f / 3f) }
    private val glowSizePx by lazy { dpToPx(24f) }

    private val tickRunnable: Runnable = object : Runnable {
        override fun run() {
            val elapsedSeconds = (System.currentTimeMillis() - startTimeMs) / 1000L
            liftMarkers.forEach { (lift, view) ->
                val count = lift.currentCount(elapsedSeconds)
                updateBadge(view, count)
            }
            handler.postDelayed(this, 1_000L)
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = FragmentMapBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // Load map image
        val bitmap = requireContext().assets.open("map.jpg").use {
            android.graphics.BitmapFactory.decodeStream(it)
        }
        binding.photoView.setImageBitmap(bitmap)
        
        // Requirements: Maxed out zoom capacity
        binding.photoView.minimumScale = 0.5f
        binding.photoView.mediumScale  = 2.5f
        binding.photoView.maximumScale = 15.0f // Increased zoom capacity

        // Requirement: Keep numbers on the coordinates when zooming/dragging
        binding.photoView.setOnMatrixChangeListener { rect ->
            updateMarkerPositions(rect)
        }

        binding.photoView.post {
            initMarkers()
            // Initial position update
            binding.photoView.displayRect?.let { updateMarkerPositions(it) }
        }
    }

    private fun initMarkers() {
        liftMarkers.clear()
        binding.markerOverlay.removeAllViews()

        val lifts = LiftRepository.load(requireContext())
        lifts.forEach { lift ->
            val marker = buildMarker(lift.currentCount(0L))
            
            // Fixed size LayoutParams, we use translation for positioning
            val lp = FrameLayout.LayoutParams(markerSizePx, markerSizePx)
            binding.markerOverlay.addView(marker, lp)
            
            liftMarkers[lift] = marker
            marker.setOnClickListener { openVideo(lift) }
        }

        startTimeMs = System.currentTimeMillis()
        handler.post(tickRunnable)
    }

    private fun updateMarkerPositions(rect: RectF) {
        liftMarkers.forEach { (lift, marker) ->
            // Pin marker to image coordinates using translation
            // rect.left/top is the offset of the zoomed image within the PhotoView
            // rect.width()/height() is the current displayed size of the image
            val px = rect.left + (lift.xPct / 100f) * rect.width()
            val py = rect.top + (lift.yPct / 100f) * rect.height()

            marker.translationX = px - markerSizePx / 2f
            marker.translationY = py - markerSizePx / 2f
            
            // Optional: scale down markers slightly when zoomed out very far, 
            // or keep them constant size. Constant size is usually better for readability.
        }
    }

    private fun buildMarker(count: Int): TextView {
        val markerBackground = buildMarkerBackground(colorForCount(count))
        return TextView(requireContext()).apply {
            text      = count.toString()
            gravity   = Gravity.CENTER
            textSize  = 11f
            setTextColor(Color.WHITE)
            setTypeface(null, Typeface.BOLD)
            background = markerBackground
            // Elevate slightly for better look on map
            elevation = 4f
        }
    }

    private fun updateBadge(view: TextView, count: Int) {
        view.text = count.toString()
        val color = colorForCount(count)
        val layers = view.background as LayerDrawable
        (layers.getDrawable(0) as GradientDrawable).setColor(withAlpha(color, 0.35f))
        (layers.getDrawable(1) as GradientDrawable).setColor(color)
    }

    private fun buildMarkerBackground(color: Int): LayerDrawable {
        val glow = GradientDrawable().apply {
            shape = GradientDrawable.OVAL
            setColor(withAlpha(color, 0.35f))
        }
        val circle = GradientDrawable().apply {
            shape = GradientDrawable.OVAL
            setColor(color)
            setStroke(dpToPx(1.2f), Color.WHITE)
        }

        val layers = LayerDrawable(arrayOf(glow, circle))
        val glowInset = ((markerSizePx - glowSizePx) / 2).coerceAtLeast(0)
        val circleInset = ((markerSizePx - circleSizePx) / 2).coerceAtLeast(0)
        layers.setLayerInset(0, glowInset, glowInset, glowInset, glowInset)
        layers.setLayerInset(1, circleInset, circleInset, circleInset, circleInset)
        return layers
    }

    private fun dpToPx(dp: Float): Int = (dp * resources.displayMetrics.density).toInt()

    private fun withAlpha(color: Int, alpha: Float): Int {
        val a = (alpha.coerceIn(0f, 1f) * 255).toInt()
        return Color.argb(a, Color.red(color), Color.green(color), Color.blue(color))
    }

    private fun colorForCount(count: Int) = when {
        count <= 5  -> Color.parseColor("#2ECC71")   // green
        count <= 12 -> Color.parseColor("#F1C40F")   // yellow
        else        -> Color.parseColor("#E74C3C")   // red
    }

    private fun openVideo(lift: LiftData) {
        VideoPlayerFragment.newInstance(lift.videoAsset, lift.name).show(
            parentFragmentManager, "video_player"
        )
    }

    override fun onPause() {
        super.onPause()
        handler.removeCallbacks(tickRunnable)
    }

    override fun onResume() {
        super.onResume()
        if (liftMarkers.isNotEmpty()) {
            handler.post(tickRunnable)
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        handler.removeCallbacks(tickRunnable)
        _binding = null
    }
}
