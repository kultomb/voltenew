package com.hbg.voltefixer

object ImsOverrideManager {

    fun getFixAllCommands(
        volte: Boolean = true,
        vowifi: Boolean = true,
        vt: Boolean = true,
        carrierCheckBypass: Boolean = true
    ): List<String> {
        val cmds = mutableListOf<String>()

        // 1. System props for VoLTE & MTK / OPPO / Qualcomm
        cmds.add("setprop persist.dbg.volte_avail_ovr 1")
        cmds.add("setprop persist.dbg.vt_avail_ovr 1")
        cmds.add("setprop persist.dbg.wfc_avail_ovr 1")
        cmds.add("setprop persist.vendor.radio.volte_mismatch_op 0")
        cmds.add("setprop persist.radio.volte_enabled_by_default 1")
        cmds.add("setprop persist.sys.cust.lte_config true")
        cmds.add("setprop persist.vendor.radio.calls.on.ims 1")

        if (carrierCheckBypass) {
            cmds.add("setprop persist.vendor.vowifi.disable.carrier.check true")
            cmds.add("setprop persist.vendor.volte.disable.carrier.check true")
            cmds.add("setprop persist.vendor.radio.disable_carrier_check true")
            cmds.add("setprop persist.vendor.radio.volte_ignore_sub 1")
        }

        // OPPO & MediaTek specific props (OPPO A5s support)
        cmds.add("setprop persist.sys.oppo.volte 1")
        cmds.add("setprop persist.radio_oppo_ct_volte_support 1")
        cmds.add("setprop persist.radio.oppo_volte_state 1")
        cmds.add("setprop persist.vendor.oppo.volte 1")
        cmds.add("setprop persist.mtk.volte.enable 1")
        cmds.add("setprop persist.mtk.volte.setting 1")
        cmds.add("setprop persist.mtk_ims_support 1")
        cmds.add("setprop persist.mtk_dynamic_ims_support 1")
        cmds.add("setprop persist.vendor.mtk_dynamic_ims_support 1")

        // 2. CarrierConfig overrides matching Pixel IMS
        val pixelConfigs = listOf(
            "carrier_volte_available_bool" to volte.toString(),
            "carrier_volte_provisioned_bool" to volte.toString(),
            "carrier_volte_provisioning_required_bool" to "false",
            "editable_enhanced_4g_lte_bool" to "true",
            "hide_enhanced_4g_lte_bool" to "false",
            "carrier_wfc_ims_available_bool" to vowifi.toString(),
            "carrier_supports_ss_over_ut_bool" to "true",
            "carrier_vowifi_offended_state_bool" to "false",
            "world_mode_enabled_bool" to "true",
            "show_4g_for_lte_data_icon_bool" to "true",
            "carrier_default_wfc_ims_enabled_bool" to vowifi.toString(),
            "carrier_vt_available_bool" to vt.toString()
        )

        val subIds = listOf("-1", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10")

        for ((key, value) in pixelConfigs) {
            cmds.add("cmd phone cc set-override $key $value")
            for (sub in subIds) {
                cmds.add("cmd phone cc set-override --sub $sub $key $value")
            }
        }

        // 3. Notify carrier config changes
        for (sub in subIds) {
            cmds.add("cmd phone cc notify --sub $sub")
            cmds.add("am broadcast -a android.telephony.action.CARRIER_CONFIG_CHANGED --ei subscription $sub")
            cmds.add("am broadcast -a android.telephony.action.CARRIER_CONFIG_CHANGED --ei android.telephony.extra.SUBSCRIPTION_INDEX $sub")
        }

        // MediaTek MT6765 & ColorOS 5.2 Direct IMS Broadcasts
        cmds.add("am broadcast -a com.mediatek.intent.action.IMS_SETTING --ei enable 1")
        cmds.add("am broadcast -a com.mediatek.ims.ACTION_IMS_SETTING_CHANGED --ei enable 1")
        cmds.add("am broadcast -a com.mediatek.intent.action.VOLTE_SETTING --ei enable 1 --ei sim_id 0")
        cmds.add("am broadcast -a com.mediatek.intent.action.VOLTE_SETTING --ei enable 1 --ei sim_id 1")
        cmds.add("am broadcast -a com.oppo.intent.action.VOLTE_STATE_CHANGE --ei state 1")
        cmds.add("am broadcast -a com.oppo.intent.action.OPPO_VOLTE_STATE_CHANGE --ei state 1")

        // 4. Global, Secure, System database injection
        val globalVal = if (volte) "1" else "0"
        val vowifiVal = if (vowifi) "1" else "0"
        val vtVal = if (vt) "1" else "0"

        for (ns in listOf("global", "secure", "system")) {
            cmds.add("settings put $ns enhanced_4g_mode_enabled $globalVal")
            cmds.add("settings put $ns carrier_volte_available_bool $globalVal")
            cmds.add("settings put $ns carrier_volte_provisioned_bool $globalVal")
            cmds.add("settings put $ns editable_enhanced_4g_lte_bool 1")
            cmds.add("settings put $ns wfc_ims_enabled $vowifiVal")
            cmds.add("settings put $ns vt_ims_enabled $vtVal")
            cmds.add("settings put $ns volte_vt_enabled $globalVal")
            cmds.add("settings put $ns oppo_volte_switch_style 1")
            cmds.add("settings put $ns oppo_vt_switch_style 1")
            cmds.add("settings put $ns volte_user_enable 1")
            cmds.add("settings put $ns oppo_volte_enable 1")
            cmds.add("settings put $ns display_volte_switch 1")
            cmds.add("settings put $ns display_vowifi_switch 1")
            cmds.add("settings put $ns config_oppo_hvolte_support_bool 1")
            cmds.add("settings put $ns config_oppo_volte_notify_stable_bool 1")
            cmds.add("settings put $ns hVolteByCarrier 1")
            cmds.add("settings put $ns KEY_HVOLTE 1")
        }

        // 5. Restart ColorOS Telephony & Settings UI
        cmds.add("am force-stop com.android.phone")
        cmds.add("am force-stop com.coloros.wirelesssettings")
        cmds.add("am force-stop com.android.settings")

        // 6. Airplane mode reset to re-register IMS
        cmds.add("cmd connectivity airplane-mode enable")
        cmds.add("cmd connectivity airplane-mode disable")

        return cmds
    }
}
