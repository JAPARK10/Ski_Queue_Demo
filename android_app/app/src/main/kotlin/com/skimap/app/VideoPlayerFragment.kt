package com.skimap.app

import android.net.Uri
import android.os.Bundle
import android.view.*
import androidx.fragment.app.DialogFragment
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.exoplayer.ExoPlayer
import com.skimap.app.databinding.FragmentVideoPlayerBinding
import java.io.File

class VideoPlayerFragment : DialogFragment() {

    companion object {
        private const val ARG_VIDEO  = "video_asset"
        private const val ARG_TITLE  = "lift_title"

        fun newInstance(videoAsset: String, title: String): VideoPlayerFragment {
            return VideoPlayerFragment().apply {
                arguments = Bundle().apply {
                    putString(ARG_VIDEO, videoAsset)
                    putString(ARG_TITLE, title)
                }
            }
        }
    }

    private var _binding: FragmentVideoPlayerBinding? = null
    private val binding get() = _binding!!
    private var player: ExoPlayer? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setStyle(STYLE_NORMAL, android.R.style.Theme_Black_NoTitleBar_Fullscreen)
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?
    ): View {
        _binding = FragmentVideoPlayerBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val videoAsset = requireArguments().getString(ARG_VIDEO, "")
        val title      = requireArguments().getString(ARG_TITLE, "Lift")

        binding.liftTitle.text = title
        binding.closeButton.setOnClickListener { dismiss() }
        // Also tap anywhere on the video surface to close
        binding.playerView.setOnClickListener { dismiss() }

        initPlayer(videoAsset)
    }

    private fun initPlayer(videoAsset: String) {
        val ctx = requireContext()

        // Copy asset to cache so ExoPlayer can read it as a file URI
        val cacheFile = File(ctx.cacheDir, videoAsset)
        if (!cacheFile.exists()) {
            ctx.assets.open("videos/$videoAsset").use { input ->
                cacheFile.outputStream().use { output -> input.copyTo(output) }
            }
        }

        player = ExoPlayer.Builder(ctx).build().also { exo ->
            binding.playerView.player = exo
            val item = MediaItem.fromUri(Uri.fromFile(cacheFile))
            exo.setMediaItem(item)
            exo.repeatMode = Player.REPEAT_MODE_ONE   // endless loop
            exo.playWhenReady = true
            exo.prepare()
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        player?.release()
        player = null
        _binding = null
    }
}
